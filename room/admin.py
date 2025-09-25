from django.contrib import admin
from .models import House, Room, Tenant, PaymentHistory

# Register your models here.
admin.site.register(House)
admin.site.register(Room)
admin.site.register(Tenant)
admin.site.register(PaymentHistory)