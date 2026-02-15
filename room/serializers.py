from rest_framework import serializers
from .models import House, Room, Tenant, PaymentHistory, TenantDocument


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class TenantDocumentSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    initial_unit = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = TenantDocument
        fields = ["id", "tenant", "document", "initial_unit"]
    def validate_tenant(self, value):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            # This should not happen if permissions are set correctly
            raise serializers.ValidationError("Could not determine user.")

        if value.room.house.owner != request.user:
            raise serializers.ValidationError(
                "You do not have permission to add documents to this tenant."
            )
        return value


class TenantSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source="room.id", read_only=True)
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), write_only=True
    )
    roomName = serializers.CharField(source="room.room_name", read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    moveInDate = serializers.DateField(source="move_in_date")
    electricityPricePerUnit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source="electricity_price_per_unit",
        required=False,
    )
    water_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    rent_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    waste_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    documents = TenantDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "roomId",
            "roomName",
            "room",
            "name",
            "contact",
            "email",
            "email_verified",
            "moveInDate",
            "electricityPricePerUnit",
            "water_price",
            "rent_price",
            "waste_price",
            "initial_unit",
            "documents",
        ]
        read_only_fields = ["email_verified"]


class PaymentHistorySerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source="room.id", read_only=True)
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), write_only=True
    )
    roomName = serializers.CharField(source="room.room_name", read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "id",
            "roomId",
            "roomName",
            "room",
            "billing_month",
            "previous_units",
            "current_units",
            "electricity",
            "payment_received_data",
            "water",
            "remarks",
            "rent",
            
            "waste",
            
            "total",
            "total_paid",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "electricity",
            "water",
            "rent",
            "waste",
            "total",
            "status",
            "created_at",
            "updated_at",
        ]



# PaymentReceived model removed; related serializer omitted
