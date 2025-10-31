from django.contrib import admin
from .models import House, Room, Tenant, PaymentHistory, TenantDocument,PaymentReceived


class TenantDocumentInline(admin.TabularInline):
    model = TenantDocument


class TenantAdmin(admin.ModelAdmin):
    inlines = [TenantDocumentInline]


# Register your models here.
admin.site.register(House)
admin.site.register(Room)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(PaymentHistory)
admin.site.register(TenantDocument)
admin.site.register(PaymentReceived)
