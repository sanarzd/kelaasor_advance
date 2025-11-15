from django.db import models
from django.utils import timezone
from users.models import CustomUser
from products.models import Product

class Ticket(models.Model):
    TICKET_CATEGORY_CHOICES = [
        ('financial', 'مالی'),
        ('support', 'پشتیبانی'),
        ('educational', 'آموزشی'),
        ('technical', 'فنی'),
        ('other', 'سایر'),
    ]

    TICKET_STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('answered', 'پاسخ داده شده'),
        ('closed', 'بسته شده'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=TICKET_CATEGORY_CHOICES, default='support')
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES, default='open')
    related_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تیکت'
        verbose_name_plural = 'تیکت‌ها'

    def __str__(self):
        return f"Ticket {self.id} - {self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.is_closed = self.status == 'closed'
        super().save(*args, **kwargs)


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender_is_user = models.BooleanField(default=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='ticket_messages_sent')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام تیکت'
        verbose_name_plural = 'پیام‌های تیکت'

    def __str__(self):
        sender_type = "User" if self.sender_is_user else "Support"
        return f"Msg {self.id} on Ticket {self.ticket.id} from {sender_type}"

    def short_message(self):
        return (self.message[:80] + '...') if len(self.message) > 80 else self.message
    short_message.short_description = "پیش‌نمایش پیام"

    def notify_user(self):
        if not self.sender_is_user and not self.is_notified:
            # TODO: ارسال اعلان یا ایمیل به کاربر
            from users.models import Notification
            Notification.objects.create(
                user=self.ticket.user,
                title=f"پاسخ به تیکت: {self.ticket.title}",
                message=self.message[:200],
                notification_type='ticket_response',
                related_url=f"/support/tickets/{self.ticket.id}/"
            )
            self.is_notified = True
            self.save()
