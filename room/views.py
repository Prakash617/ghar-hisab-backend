from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import House, Room, Tenant, PaymentHistory
from .serializers import HouseSerializer, RoomSerializer, TenantSerializer, PaymentHistorySerializer

class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(house__owner=self.request.user)
        house_id = self.request.query_params.get('house_id')
        if house_id:
            queryset = queryset.filter(house__id=house_id)
        return queryset

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(room__house__owner=self.request.user)
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room__id=room_id)
        return queryset

class PaymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = PaymentHistory.objects.all()
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]
    ordering = ['id', '-created_at']

    def get_queryset(self):
        queryset = self.queryset.filter(room__house__owner=self.request.user)
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room__id=room_id)
        return queryset