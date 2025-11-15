from django.urls import path
from .views import TicketListCreateView, TicketDetailView, TicketMessageCreateView

urlpatterns = [
    path('tickets/', TicketListCreateView.as_view(), name='tickets-list'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:ticket_id>/messages/', TicketMessageCreateView.as_view(), name='ticket-messages-create'),
]
