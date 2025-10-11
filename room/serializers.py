from rest_framework import serializers
from .models import House, Room, Tenant, PaymentHistory, TenantDocument, PaymentReceived

class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class TenantDocumentSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    class Meta:
        model = TenantDocument
        fields = ['id', 'tenant', 'document']

    def validate_tenant(self, value):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            # This should not happen if permissions are set correctly
            raise serializers.ValidationError("Could not determine user.")

        if value.room.house.owner != request.user:
            raise serializers.ValidationError("You do not have permission to add documents to this tenant.")
        return value

class TenantSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room.id', read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)
    moveInDate = serializers.DateField(source='move_in_date')
    electricityPricePerUnit = serializers.DecimalField(max_digits=10, decimal_places=2, source='electricity_price_per_unit', required=False)
    water_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    rent_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    waste_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    documents = TenantDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'roomId', 'room', 'name', 'contact', 'moveInDate', 'electricityPricePerUnit',
            'water_price', 'rent_price', 'waste_price',
            'documents'
        ]

class PaymentHistorySerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room.id', read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'roomId', 'room', 'billing_month', 'previous_units', 'current_units',
            'electricity', 'electricity_paid', 'electricity_status', 'electricity_updated_at',
            'water', 'water_paid', 'water_status', 'water_updated_at',
            'rent', 'rent_paid', 'rent_status', 'rent_updated_at',
            'waste', 'waste_paid', 'waste_status', 'waste_updated_at',
            'total', 'total_paid', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'electricity', 'water', 'rent', 'waste', 'total',
            'electricity_status', 'water_status', 'rent_status', 'waste_status', 'status',
            'total_paid', 'created_at', 'updated_at',
            'electricity_updated_at', 'water_updated_at', 'rent_updated_at', 'waste_updated_at'
        ]
        
class PaymentReceivedSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True)
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all(), write_only=True)
    total_amount_due = serializers.SerializerMethodField()

    class Meta:
        model = PaymentReceived
        fields = [
            'id',
            'tenant_id',
            'tenant',
            'amount',
            'received_date',
            'remarks',
            'status',
            'created_at',
            'total_amount_due',
        ]
        read_only_fields = ('status', 'created_at', 'total_amount_due')

    def get_total_amount_due(self, obj):
        from django.db.models import Sum
        total_due = PaymentHistory.objects.filter(room__tenant=obj.tenant).aggregate(
            total_due=Sum('total')
        )['total_due'] or 0
        return total_due