from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    Cart, CartItem, Order, OrderItem, CourseEnrollment, Notification,
    UserProfile, DiscountCode, PaymentHistory
)
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, UserSerializer, CartSerializer,
    AddToCartSerializer, RemoveFromCartSerializer, CheckoutSerializer,
    UserProfileSerializer, NotificationSerializer
)
from django.shortcuts import get_object_or_404
from products.models import Product


class SendOTPView(generics.CreateAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [permissions.AllowAny]


class VerifyOTPView(generics.CreateAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response({"message": "ورود موفق", "user_id": user.id, "phone": user.phone})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        unread = request.user.notifications.filter(is_read=False).count()
        data = serializer.data
        data['unread_notifications'] = unread
        return Response(data)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(generics.CreateAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({'message': 'Added to cart', 'item_id': item.id}, status=status.HTTP_201_CREATED)


class RemoveFromCartView(generics.CreateAPIView):
    serializer_class = RemoveFromCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Removed from cart'}, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.is_complete():
            return Response({
                'detail': 'لطفاً اطلاعات پروفایل خود را تکمیل کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            return Response({'detail': 'سبد خرید خالی است.'}, status=status.HTTP_400_BAD_REQUEST)

        for item in cart.items.all():
            if CourseEnrollment.objects.filter(user=request.user, product=item.product).exists():
                return Response({'detail': f'دوره "{item.product.title}" قبلاً خریداری شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.product.price for item in cart.items.all())

        discount_code_str = request.data.get('discount_code')
        discount_code = None
        if discount_code_str:
            try:
                discount_code = DiscountCode.objects.get(code=discount_code_str)
            except DiscountCode.DoesNotExist:
                return Response({'detail': 'کد تخفیف نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)
            if not discount_code.is_valid(user=request.user):
                return Response({'detail': 'کد تخفیف منقضی یا نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)
            total = discount_code.apply_discount_for_item(total)
            discount_code.used_count += 1
            discount_code.save()

        order = Order.objects.create(user=request.user, total=total, discount_code=discount_code)

        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, price=item.product.price)
            access_expires_at = None
            if item.product.course_type == 'offline' and item.product.access_expiration:
                access_expires_at = timezone.make_aware(item.product.access_expiration)
            CourseEnrollment.objects.create(
                user=request.user,
                product=item.product,
                order=order,
                access_expires_at=access_expires_at,
                is_active=True
            )

        PaymentHistory.objects.create(
            order=order,
            amount=total,
            status='completed',
            payment_method='manual'
        )

        Notification.objects.create(
            user=request.user,
            title='سفارش ثبت شد',
            message=f'سفارش شماره {order.id} با موفقیت ثبت شد.',
            notification_type='order_confirmed'
        )

        cart.items.all().delete()

        return Response({
            'message': 'سفارش با موفقیت ثبت شد.',
            'order_id': order.id,
            'total': str(total)
        }, status=status.HTTP_201_CREATED)


class MyCoursesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        enrollments = CourseEnrollment.objects.filter(user=request.user, is_active=True)
        data = [{
            'product_id': e.product.id,
            'title': e.product.title,
            'course_type': e.product.course_type,
            'has_access': e.has_access(),
            'enrolled_at': e.enrolled_at
        } for e in enrollments]
        return Response(data)


class OrdersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        data = []
        for o in orders:
            items = [{'product': it.product.title, 'price': str(it.price)} for it in o.items.all()]
            data.append({'id': o.id, 'total': str(o.total), 'created_at': o.created_at, 'items': items})
        return Response(data)


class NotificationsListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'message': 'Marked as read'})

