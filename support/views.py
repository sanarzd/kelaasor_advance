from rest_framework import generics, permissions
from .models import Ticket, TicketMessage
from .serializers import TicketSerializer, TicketMessageSerializer
from rest_framework.exceptions import NotFound


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


class TicketMessageCreateView(generics.CreateAPIView):
    serializer_class = TicketMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        try:
            ticket = Ticket.objects.get(pk=ticket_id, user=self.request.user)
        except Ticket.DoesNotExist:
            raise NotFound('تیکت یافت نشد یا شما دسترسی ندارید.')
        
        serializer.save(ticket=ticket, sender_is_user=True)
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save(update_fields=['status'])


