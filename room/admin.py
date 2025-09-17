from django.contrib import admin
from .models import Room, Tenant, PaymentHistory

# Register your models here.
admin.site.register(Room)
admin.site.register(Tenant)
admin.site.register(PaymentHistory)