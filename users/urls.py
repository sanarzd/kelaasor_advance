from django.urls import path
from .views import (
    SendOTPView, VerifyOTPView, MeView, CartView,
    AddToCartView, RemoveFromCartView, CheckoutView, OrdersListView,
    UserProfileView, NotificationsListView, NotificationMarkReadView
)

urlpatterns = [
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="cart-add"),
    path("cart/remove/", RemoveFromCartView.as_view(), name="cart-remove"),
    path("cart/checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrdersListView.as_view(), name="orders-list"),
    path("notifications/", NotificationsListView.as_view(), name="notifications-list"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
]