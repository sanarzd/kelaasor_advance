from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from .models import (
    CustomUser, OTP, Cart, CartItem, Order, OrderItem, CourseEnrollment,
    UserProfile, DiscountCode, PaymentHistory, Notification
)
from products.models import Product
from django.utils import timezone
from decimal import Decimal


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "phone", "first_name", "last_name", "is_phone_verified", "email"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "user", "city", "address", "birth_date", "updated_at"]
        read_only_fields = ["user", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "notification_type", "is_read", "created_at", "related_url"]
        read_only_fields = ["created_at"]


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def create(self, validated_data):
        phone = validated_data["phone"]
        otp = OTP.create_otp(phone)
        return otp


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        phone = attrs["phone"]
        code = attrs["code"]
        otp = OTP.objects.filter(phone=phone).order_by("-created_at").first()
        if not otp or not otp.is_valid() or otp.code != code:
            raise serializers.ValidationError("کد وارد شده نادرست یا منقضی است.")
        user, created = CustomUser.objects.get_or_create(phone=phone)
        user.is_phone_verified = True
        user.save()
        attrs["user"] = user
        return attrs


class ProductSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "price"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total"]
        read_only_fields = ["user"]

    def get_total(self, obj):
        return obj.total_price()


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Product not found.')
        user = self.context['request'].user
        if CourseEnrollment.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError('You have already purchased this course.')
        if product.course_type == 'online' and product.registration_deadline and timezone.now().date() > product.registration_deadline:
            raise serializers.ValidationError('Registration deadline has passed for this course.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        product = Product.objects.get(pk=validated_data['product_id'])
        cart, _ = Cart.objects.get_or_create(user=user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            raise serializers.ValidationError('This course is already in your cart.')
        return item


class RemoveFromCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        try:
            Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Product not found.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            raise serializers.ValidationError('Cart not found.')
        product = Product.objects.get(pk=self.validated_data['product_id'])
        CartItem.objects.filter(cart=cart, product=product).delete()
        return {}


class CheckoutSerializer(serializers.Serializer):
    discount_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    payment_method = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context['request'].user
        cart = Cart.objects.filter(user=user).first()
        if not cart or not cart.items.exists():
            raise serializers.ValidationError('Cart is empty.')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.is_complete():
            raise serializers.ValidationError('Please complete your profile before checkout.')
        discount_code = attrs.get('discount_code') or None
        if discount_code:
            try:
                dc = DiscountCode.objects.get(code=discount_code)
            except DiscountCode.DoesNotExist:
                raise serializers.ValidationError('Invalid discount code.')
            if not dc.is_valid(user=user):
                raise serializers.ValidationError('Discount code is not valid or expired.')
            attrs['discount_obj'] = dc
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.get(user=user)
        discount_obj = validated_data.get('discount_obj', None)
        with transaction.atomic():
            total = Decimal('0.00')
            items = list(cart.items.select_related('product').all())
            for item in items:
                price = item.product.price
                if discount_obj:
                    price = discount_obj.apply_discount_for_item(price, product=item.product)
                total += price

            order = Order.objects.create(user=user, total=total, discount_code=discount_obj if discount_obj else None)

            from django.utils import timezone as _tz, datetime as _dt
            for item in items:
                OrderItem.objects.create(order=order, product=item.product, price=item.product.price)

                access_expires_at = None
                if item.product.course_type == 'offline' and item.product.access_expiration:
                    access_expires_at = _tz.make_aware(_dt.datetime.combine(item.product.access_expiration, _dt.datetime.min.time()))
                CourseEnrollment.objects.create(user=user, product=item.product, order=order, access_expires_at=access_expires_at, is_active=True)

            cart.items.all().delete()

            if discount_obj:
                DiscountCode.objects.filter(pk=discount_obj.pk).update(used_count=F('used_count') + 1)

            ph = PaymentHistory.objects.create(
                order=order,
                amount=total,
                status='pending',
                payment_method=validated_data.get('payment_method', ''),
                transaction_id=None
            )

            Notification.objects.create(
                user=user,
                title="سفارش ثبت شد",
                message=f"سفارش {order.id} با موفقیت ثبت شد.",
                notification_type='order_confirmed',
                related_url=f"/orders/{order.id}/"
            )

            return {'order': order, 'payment': ph}
