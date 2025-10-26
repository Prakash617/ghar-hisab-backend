from rest_framework import viewsets, mixins, status, serializers
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import House, Room, Tenant, PaymentHistory, TenantDocument, PaymentReceived
from .serializers import (
    HouseSerializer,
    RoomSerializer,
    TenantSerializer,
    PaymentHistorySerializer,
    TenantDocumentSerializer,
    PaymentReceivedSerializer,
)


class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform__create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "message": "House and all associated rooms, tenants, and payment history have been deleted."
            },
            status=status.HTTP_200_OK,
        )


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(house__owner=self.request.user)
        house_id = self.request.query_params.get("house_id")
        if house_id:
            queryset = queryset.filter(house__id=house_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Room and associated tenant deleted successfully."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def tenant(self, request, pk=None):
        """
        Return the tenant associated with the room.
        """
        room = self.get_object()
        if hasattr(room, "tenant"):
            serializer = TenantSerializer(room.tenant)
            return Response(serializer.data)
        else:
            return Response(status=404)

    @action(detail=False, methods=["post"], url_path="create-with-tenant")
    def create_with_tenant(self, request):
        """
        Create a room and a tenant for it in one go.
        Accepts a flat structure for room details and a nested 'tenant' object.
        """
        data = request.data.copy()
        tenant_data = data.pop("tenant", None)
        room_data = data

        if not tenant_data:
            return Response(
                {"error": "'tenant' data is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "house" not in room_data:
            return Response(
                {"error": "House is required for a room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            house = House.objects.get(pk=room_data["house"])
            if house.owner != request.user:
                return Response(
                    {"error": "You do not have permission for this house."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except House.DoesNotExist:
            return Response(
                {"error": "House not found."}, status=status.HTTP_404_NOT_FOUND
            )

        room_serializer = self.get_serializer(data=room_data)
        if not room_serializer.is_valid():
            return Response(room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                room = room_serializer.save()

                room.is_occupied = True
                room.save()

                tenant_data["room"] = room.id
                tenant_serializer = TenantSerializer(
                    data=tenant_data, context={"request": request}
                )
                if not tenant_serializer.is_valid():
                    raise serializers.ValidationError(tenant_serializer.errors)

                tenant_serializer.save()

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"room": room_serializer.data, "tenant": tenant_serializer.data},
            status=status.HTTP_201_CREATED,
        )


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = self.queryset.filter(room__house__owner=self.request.user)
        room_id = self.request.query_params.get("room_id")
        if room_id:
            queryset = queryset.filter(room__id=room_id)
        return queryset


class PaymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = PaymentHistory.objects.all()
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(room__house__owner=self.request.user)
        room_id = self.request.query_params.get("room_id")
        if room_id:
            queryset = queryset.filter(room__id=room_id)
        return queryset.order_by("-created_at", "id")


class TenantDocumentViewSet(viewsets.ModelViewSet):
    queryset = TenantDocument.objects.all()
    serializer_class = TenantDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return self.queryset.filter(tenant__room__house__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        tenant_id = request.data.get("tenant")
        initial_unit = request.data.get("initial_unit")

        if not tenant_id:
            return Response(
                {"error": "Tenant is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            if tenant.room.house.owner != request.user:
                return Response(
                    {"error": "You do not have permission for this tenant."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Tenant.DoesNotExist:
            return Response(
                {"error": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if initial_unit is not None:
            tenant.initial_unit = initial_unit
            tenant.save()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "File deleted successfully"}, status=200)


class PaymentReceivedViewSet(viewsets.ModelViewSet):
    queryset = PaymentReceived.objects.all()
    serializer_class = PaymentReceivedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(tenant__room__house__owner=self.request.user)
        tenant_id = self.request.query_params.get("tenant_id")
        if tenant_id:
            queryset = queryset.filter(tenant__id=tenant_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Payment record deleted successfully."},
            status=status.HTTP_200_OK,
        )
