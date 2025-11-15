from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from decimal import Decimal
from products.models import Product
import random, string


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return f"{self.phone} ({self.first_name or ''} {self.last_name or ''})"


class OTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @classmethod
    def create_otp(cls, phone):
        last_otp = cls.objects.filter(phone=phone).order_by("-created_at").first()
        if last_otp and (timezone.now() - last_otp.created_at).total_seconds() < 60:
            raise ValueError("لطفاً یک دقیقه صبر کنید و دوباره تلاش کنید.")
        cls.objects.filter(phone=phone).delete()
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=5)
        return cls.objects.create(phone=phone, code=code, expires_at=expires_at)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.phone}"


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران"

    def __str__(self):
        return f"پروفایل {self.user.phone}"

    def is_complete(self):
        return bool(self.city and self.address and self.birth_date)


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cart")

    def total_price(self):
        return sum(item.product.price for item in self.items.all())

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد خرید {self.user.phone}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["cart", "product"]
        verbose_name = "آیتم سبد خرید"
        verbose_name_plural = "آیتم‌های سبد خرید"

    def __str__(self):
        return f"{self.product.title} در سبد {self.cart.user.phone}"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_code = models.ForeignKey('DiscountCode', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"

    def __str__(self):
        return f"سفارش {self.id} از {self.user.phone}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.product.title} در سفارش {self.order.id}"


class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'درصدی'),
        ('amount', 'مبلغ ثابت'),
    ]
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    max_usage = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return f"{self.code} ({self.discount_type})"

    def is_valid(self, user=None, product=None):
        now = timezone.now()
        if not self.is_active or (self.start_date and self.start_date > now) or (self.end_date and self.end_date < now):
            return False
        if self.max_usage and self.used_count >= self.max_usage:
            return False
        if self.user and (not user or self.user != user):
            return False
        if self.product and (not product or self.product != product):
            return False
        return True

    def apply_discount_for_item(self, price, product=None):
        if self.product and product and self.product != product:
            return price
        if self.discount_type == 'percent':
            discount_amount = (self.value / Decimal(100)) * price
            return max(price - discount_amount, Decimal('0.00'))
        if self.discount_type == 'amount':
            return max(price - self.value, Decimal('0.00'))
        return price


class PaymentHistory(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('refunded', 'بازگشت وجه'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تاریخچه پرداخت"
        verbose_name_plural = "تاریخچه پرداخت‌ها"

    def __str__(self):
        return f"Payment {self.id} for order {self.order.id} - {self.status}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ("ticket_response", "پاسخ تیکت"),
        ("order_confirmed", "تایید سفارش"),
        ("course_started", "شروع دوره"),
        ("offer", "تخفیف یا پیشنهاد"),
        ("general", "عمومی"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default="general")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اطلاع‌رسانی"
        verbose_name_plural = "اطلاع‌رسانی‌ها"

    def __str__(self):
        return f"اعلان برای {self.user.phone}: {self.title}"


class CourseEnrollment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="enrollments")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="enrollments")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="enrollments", null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "product"]
        ordering = ["-enrolled_at"]
        verbose_name = "ثبت‌نام کاربر"
        verbose_name_plural = "ثبت‌نام کاربران"

    def __str__(self):
        return f"{self.user.phone} در دوره {self.product.title}"

    def has_access(self):
        if not self.is_active:
            return False
        if self.product.course_type == "offline" and self.access_expires_at:
            return timezone.now() < self.access_expires_at
        if self.product.course_type == "online" and self.product.registration_deadline:
            return timezone.now().date() <= self.product.registration_deadline
        return True



