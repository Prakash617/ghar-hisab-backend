from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum


class House(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, null=True)
    room_name = models.CharField(max_length=100,blank=True, null=True)
    room_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        if self.house:
            return f"{self.house.name} - {self.room_number}"
        return self.room_number


class Tenant(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name="tenant")
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    move_in_date = models.CharField(max_length=40)
    electricity_price_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, default=15.00
    )
    water_price = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    waste_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    initial_unit = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class TenantDocument(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="documents"
    )
    document = models.FileField(upload_to="tenant_documents/")
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Document for {self.tenant.name}"

from django.utils import timezone

def current_billing_month():
    return timezone.now().strftime("%Y-%m")

def current_date_str():
    return timezone.now().strftime("%Y-%m-%d")

class PaymentHistory(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Unpaid", "Unpaid"),
        ("Partially Paid", "Partially Paid"),
    ]

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="payment_history"
    )
    billing_month = models.CharField(
        max_length=50, default=current_billing_month
    )  # better than DateField for consistency

    previous_units = models.IntegerField()
    current_units = models.IntegerField()

    electricity = models.DecimalField(max_digits=10, decimal_places=2)
    # payment tracking is stored in `payment_received_data` instead of per-item fields

    water = models.DecimalField(max_digits=10, decimal_places=2)
    

    rent = models.DecimalField(max_digits=10, decimal_places=2)
    

    waste = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    

    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    # Records summary of payments received (e.g. JSON/string with amounts, dates)
    payment_received_date = models.CharField(max_length=500, null=True, blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remarks = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Unpaid"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # updates automatically

    def __str__(self):
        return f"Payment for {self.room} - {self.billing_month}"

    def clean(self):
        if self.previous_units >= self.current_units:
            raise ValidationError("Previous unit must be less than current unit.")

    def save(self, *args, **kwargs):
        if not self.pk:  # if the instance is new
            tenant = self.room.tenant
            last_payment = (
                PaymentHistory.objects.filter(room=self.room).order_by("-billing_month").first()
            )
            if last_payment:
                self.previous_units = last_payment.current_units
            else:
                self.previous_units = tenant.initial_unit
            self.electricity = (
                self.current_units - self.previous_units
            ) * tenant.electricity_price_per_unit
            self.water = tenant.water_price
            self.rent = tenant.rent_price
            self.waste = tenant.waste_price
        else:
            # on update, don't attempt to track per-item paid fields (removed)
            pass

        # Auto calculate total
        # Auto calculate total; `total_paid` is set from `payment_received_data` or provided directly
        self.total = self.electricity + self.water + self.rent + self.waste
        self.status = self._get_status(self.total, self.total_paid)

        super().save(*args, **kwargs)

    def _get_status(self, amount, paid):
        if paid == 0:
            return "Unpaid"
        elif paid < amount:
            return "Partially Paid"
        return "Paid"
