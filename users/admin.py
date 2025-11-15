from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, UserProfile, OTP, Cart, CartItem, Order, OrderItem,
    DiscountCode, Notification, PaymentHistory, CourseEnrollment
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('phone', 'email', 'is_staff', 'is_phone_verified', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_phone_verified')
    ordering = ('phone',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'is_phone_verified')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('phone', 'email', 'first_name', 'last_name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'updated_at')
    list_filter = ('city',)
    search_fields = ('user__phone', 'user__email')
    readonly_fields = ('updated_at',)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('created_at',)
    search_fields = ('phone',)
    readonly_fields = ('created_at', 'expires_at')

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'معتبر'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'items_count')
    search_fields = ('user__phone', 'user__email')

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'تعداد آیتم‌ها'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product')
    list_filter = ('product__course_type',)
    search_fields = ('cart__user__phone', 'product__title')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'created_at', 'items_count', 'discount_code')
    list_filter = ('created_at',)
    search_fields = ('user__phone', 'user__email')
    readonly_fields = ('created_at',)

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'تعداد آیتم‌ها'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price')
    list_filter = ('product__course_type',)
    search_fields = ('order__user__phone', 'product__title')


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'is_active', 'start_date', 'end_date', 'user', 'product', 'used_count', 'max_usage')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)
    readonly_fields = ('used_count',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__phone', 'title', 'message')
    readonly_fields = ('created_at',)


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'payment_method', 'paid_at', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order__user__phone', 'transaction_id')
    readonly_fields = ('created_at',)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'product__course_type', 'enrolled_at')
    search_fields = ('user__phone', 'product__title')
    readonly_fields = ('enrolled_at',)

