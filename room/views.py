from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Room, Tenant, PaymentHistory
from .serializers import RoomSerializer, TenantSerializer, PaymentHistorySerializer

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter tenants based on the rooms owned by the user
        return self.queryset.filter(room__owner=self.request.user)

class PaymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = PaymentHistory.objects.all()
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter payment history based on the rooms owned by the user
        return self.queryset.filter(room__owner=self.request.user)