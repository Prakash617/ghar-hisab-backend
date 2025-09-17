from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    room_number = models.CharField(max_length=10)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return self.room_number

class Tenant(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='tenant')
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    move_in_date = models.DateField()
    document = models.FileField(upload_to='tenant_documents/', blank=True, null=True)

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

    def __str__(self):
        return f"Payment for {self.room.room_number} - {self.month}"