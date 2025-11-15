from rest_framework import serializers
from .models import Ticket, TicketMessage

class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ['id', 'sender_is_user', 'message']
        read_only_fields = ['sender_is_user', 'created_at']

class TicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'title', 'message', 'category', 'status',
            'related_product', 'created_at', 'is_closed', 'messages'
        ]
        read_only_fields = ['user', 'status', 'created_at', 'is_closed']