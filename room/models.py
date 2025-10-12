from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

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
    electricity_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)
    water_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    waste_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class TenantDocument(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='tenant_documents/')

    def __str__(self):
        return f"Document for {self.tenant.name}"

class PaymentHistory(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='payment_history')
    billing_month = models.DateField(default=timezone.now)  # better than CharField for consistency
    
    previous_units = models.IntegerField()
    current_units = models.IntegerField()
    
    electricity = models.DecimalField(max_digits=10, decimal_places=2)
    electricity_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    electricity_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    electricity_updated_at = models.DateTimeField(null=True, blank=True)
    
    water = models.DecimalField(max_digits=10, decimal_places=2)
    water_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    water_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    water_updated_at = models.DateTimeField(null=True, blank=True)
    
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    rent_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rent_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    rent_updated_at = models.DateTimeField(null=True, blank=True)
    
    waste = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    waste_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    waste_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    waste_updated_at = models.DateTimeField(null=True, blank=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # updates automatically

    def __str__(self):
        return f"Payment for {self.room} - {self.billing_month.strftime('%B %Y')}"

    def clean(self):
        if self.previous_units >= self.current_units:
            raise ValidationError('Previous unit must be less than current unit.')

    def save(self, *args, **kwargs):
        if not self.pk:  # if the instance is new
            tenant = self.room.tenant
            self.electricity = (self.current_units - self.previous_units) * tenant.electricity_price_per_unit
            self.water = tenant.water_price
            self.rent = tenant.rent_price
            self.waste = tenant.waste_price
        else:
            original = PaymentHistory.objects.get(pk=self.pk)
            if self.electricity_paid != original.electricity_paid:
                self.electricity_updated_at = timezone.now()
            if self.water_paid != original.water_paid:
                self.water_updated_at = timezone.now()
            if self.rent_paid != original.rent_paid:
                self.rent_updated_at = timezone.now()
            if self.waste_paid != original.waste_paid:
                self.waste_updated_at = timezone.now()

        # Auto calculate total
        self.total = self.electricity + self.water + self.rent + self.waste
        self.total_paid = self.electricity_paid + self.water_paid + self.rent_paid + self.waste_paid

        # Update statuses
        self.electricity_status = self._get_status(self.electricity, self.electricity_paid)
        self.water_status = self._get_status(self.water, self.water_paid)
        self.rent_status = self._get_status(self.rent, self.rent_paid)
        self.waste_status = self._get_status(self.waste, self.waste_paid)
        self.status = self._get_status(self.total, self.total_paid)

        super().save(*args, **kwargs)

    def _get_status(self, amount, paid):
        if paid == 0:
            return 'Unpaid'
        elif paid < amount:
            return 'Partially Paid'
        return 'Paid'


class PaymentReceived(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Unpaid', 'Unpaid'),
        ('Overpaid', 'Overpaid'),
    ]

    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='Unpaid',
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.name} ({self.amount}) on {self.received_date} - {self.status}"

    def save(self, *args, **kwargs):
        """When a payment is saved, update the tenant's overall payment status."""
        super().save(*args, **kwargs)
        self.update_payment_status()

    def update_payment_status(self):
        """Calculate the payment status of this tenant from PaymentHistory totals."""
        from .models import PaymentHistory  # avoid circular import

        # Total amount due across all histories
        total_due = PaymentHistory.objects.filter(room__tenant=self.tenant).aggregate(
            total_due=Sum('total')
        )['total_due'] or 0

        # Total amount received from this tenant
        total_received = PaymentReceived.objects.filter(tenant=self.tenant).aggregate(
            total_received=Sum('amount')
        )['total_received'] or 0

        # Determine payment status
        if total_received == 0:
            status = 'Unpaid'
        elif total_received < total_due:
            status = 'Partially Paid'
        elif total_received > total_due:
            status = 'Overpaid'
        else:
            status = 'Paid'

        # Update status for all tenant payments (keep them consistent)
        PaymentReceived.objects.filter(tenant=self.tenant).update(status=status)