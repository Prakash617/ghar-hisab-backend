from rest_framework import serializers
from .models import House, Room, Tenant, PaymentHistory

class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class TenantSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room.id', read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)
    moveInDate = serializers.DateField(source='move_in_date')
    electricityPricePerUnit = serializers.DecimalField(max_digits=10, decimal_places=2, source='electricity_price_per_unit')

    class Meta:
        model = Tenant
        fields = [
            'id', 'roomId', 'room', 'name', 'contact', 'moveInDate', 'electricityPricePerUnit'
        ]

class PaymentHistorySerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room.id', read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)
    previous_units = serializers.IntegerField()
    current_units = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'roomId', 'room', 'month', 'previous_units', 'current_units',
            'electricity', 'water', 'rent', 'total', 'status',
            'electricity_status', 'water_status', 'rent_status'
        ]
        extra_kwargs = {
            'room': {'required': False},
            'previous_units': {'required': False},
            'current_units': {'required': False},
            'electricity': {'required': False},
            'water': {'required': False},
            'rent': {'required': False},
        }

    def to_internal_value(self, data):
        for field in ['electricity', 'water', 'rent']:
            if field in data and isinstance(data[field], dict):
                if 'amount' in data[field]:
                    data[f'{field}_status'] = data[field].get('status', 'Unpaid')
                    data[field] = data[field]['amount']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['electricity'] = {
            "amount": instance.electricity,
            "status": instance.electricity_status
        }
        representation['water'] = {
            "amount": instance.water,
            "status": instance.water_status
        }
        representation['rent'] = {
            "amount": instance.rent,
            "status": instance.rent_status
        }
        representation['total'] = {
            "amount": instance.total,
            "status": instance.status
        }
        return representation

    def validate(self, data):
        previous_units = data.get('previous_units', getattr(self.instance, 'previous_units', None))
        current_units = data.get('current_units', getattr(self.instance, 'current_units', None))

        if previous_units is not None and current_units is not None and previous_units = current_units:
            raise serializers.ValidationError("Previous unit must be less than current unit.")
        return data

    def _calculate_overall_status(self, validated_data):
        statuses = [
            validated_data.get('electricity_status', 'Unpaid'),
            validated_data.get('water_status', 'Unpaid'),
            validated_data.get('rent_status', 'Unpaid')
        ]
        if all(s == 'Paid' for s in statuses):
            return 'Paid'
        elif any(s == 'Paid' for s in statuses):
            return 'Partially Paid'
        else:
            return 'Unpaid'

    def create(self, validated_data):
        room = validated_data['room']
        previous_units = validated_data['previous_units']
        current_units = validated_data['current_units']

        print(f"DEBUG: Room ID: {room.id}")
        print(f"DEBUG: Room object: {room}")
        print(f"DEBUG: Has tenant: {hasattr(room, 'tenant')}")

        if hasattr(room, 'tenant'):
            print(f"DEBUG: Tenant found for room {room.id}")
            electricity_price_per_unit = room.tenant.electricity_price_per_unit
            validated_data['electricity'] = (current_units - previous_units) * electricity_price_per_unit
            print(f"DEBUG: Calculated electricity: {validated_data['electricity']}")
        else:
            print(f"DEBUG: No tenant found for room {room.id}. Electricity set to 0.")
            validated_data['electricity'] = 0 # Ensure it's explicitly set to 0 if no tenant

        water = validated_data.get('water', 0)
        rent = validated_data.get('rent', 0)
        validated_data['total'] = validated_data.get('electricity', 0) + water + rent
        validated_data['status'] = self._calculate_overall_status(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'previous_units' in validated_data or 'current_units' in validated_data:
            previous_units = validated_data.get('previous_units', instance.previous_units)
            current_units = validated_data.get('current_units', instance.current_units)
            if hasattr(instance.room, 'tenant'):
                electricity_price_per_unit = instance.room.tenant.electricity_price_per_unit
                validated_data['electricity'] = (current_units - previous_units) * electricity_price_per_unit

        instance = super().update(instance, validated_data)

        instance.total = instance.electricity + instance.water + instance.rent
        instance.status = self._calculate_overall_status({
            'electricity_status': instance.electricity_status,
            'water_status': instance.water_status,
            'rent_status': instance.rent_status
        })
        instance.save()
        return instance