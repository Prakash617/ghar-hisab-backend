from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class House(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Room(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, null=True)
    room_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        if self.house:
            return f"{self.house.name} - {self.room_number}"
        return self.room_number

class Tenant(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='tenant')
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    move_in_date = models.DateField()
    document = models.FileField(upload_to='tenant_documents/', blank=True, null=True)
    electricity_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)

    def __str__(self):
        return self.name

class PaymentHistory(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='payment_history')
    month = models.CharField(max_length=50,blank=False)
    previous_units = models.IntegerField()
    current_units = models.IntegerField()
    electricity = models.DecimalField(max_digits=10, decimal_places=2)
    water = models.DecimalField(max_digits=10, decimal_places=2)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    electricity_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    water_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    rent_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment for {self.room} - {self.month}"

    def save(self, *args, **kwargs):
        if self.previous_units >= self.current_units:
            raise ValidationError('Previous unit must be less than current unit.')
        super().save(*args, **kwargs)