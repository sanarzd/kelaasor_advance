from django.contrib import admin
from .models import Ticket, TicketMessage

class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('sender_is_user', 'sender', 'message', 'created_at', 'is_notified')
    ordering = ('created_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'category', 'status', 'related_product', 'created_at', 'is_closed')
    list_filter = ('category', 'status', 'is_closed', 'created_at')
    search_fields = ('title', 'message', 'user__email', 'user__phone')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'related_product')
    inlines = [TicketMessageInline]
    fieldsets = (
        ('اطلاعات تیکت', {
            'fields': ('user', 'title', 'message', 'category', 'status', 'related_product')
        }),
        ('وضعیت', {
            'fields': ('is_closed', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_as_answered', 'close_tickets']

    def mark_as_answered(self, request, queryset):
        count = queryset.update(status='answered', is_closed=False)
        self.message_user(request, f'{count} تیکت به عنوان پاسخ داده شده علامت‌گذاری شد.')
    mark_as_answered.short_description = 'علامت‌گذاری به عنوان پاسخ داده شده'

    def close_tickets(self, request, queryset):
        count = queryset.update(status='closed', is_closed=True)
        self.message_user(request, f'{count} تیکت بسته شد.')
    close_tickets.short_description = 'بستن تیکت‌ها'


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'sender_is_user', 'sender', 'created_at', 'is_notified', 'short_message')
    list_filter = ('sender_is_user', 'is_notified', 'created_at')
    search_fields = ('ticket__title', 'message', 'sender__email')
    readonly_fields = ('created_at',)
    ordering = ('created_at',)

