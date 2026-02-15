from django.contrib import admin
from .models import House, Room, Tenant, PaymentHistory, TenantDocument


class HouseAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active")
    list_filter = ("is_active", "owner")
    search_fields = ("name", "owner__username")


class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "room_number", "house", "is_occupied")
    list_filter = ("is_occupied", "house")
    search_fields = ("room_name", "room_number", "house__name")


class TenantDocumentInline(admin.TabularInline):
    model = TenantDocument
    extra = 1  # Number of empty forms to display


class TenantAdmin(admin.ModelAdmin):
    inlines = [TenantDocumentInline]
    list_display = (
        "name",
        "room",
        "contact",
        "move_in_date",
        "electricity_price_per_unit",
        "water_price",
        "rent_price",
        "waste_price",
    )
    list_filter = ("room__house", "room__is_occupied")
    search_fields = ("name", "contact", "room__room_number", "room__house__name")
    readonly_fields = (
        "electricity_price_per_unit",
        "water_price",
        "rent_price",
        "waste_price",
        "initial_unit",
    )
    fieldsets = (
        (None, {"fields": ("room", "name", "contact", "move_in_date")}),
        (
            "Pricing Details (Read-only)",
            {
                "fields": (
                    "electricity_price_per_unit",
                    "water_price",
                    "rent_price",
                    "waste_price",
                    "initial_unit",
                ),
                "classes": ("collapse",),
            },
        ),
    )


class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "billing_month",
        "previous_units",
        "current_units",
        "electricity",
        "water",
        "rent",
        "waste",
        "total",
        "total_paid",
        "status",
        "created_at",
    )
    list_filter = ("status", "billing_month", "room__house", "room")
    search_fields = ("room__room_number", "billing_month")
    readonly_fields = (
        "electricity",
        "water",
        "rent",
        "waste",
        "total",
        "status",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("room", "billing_month", "previous_units", "current_units")}),
        (
            "Calculated Details (Read-only)",
            {
                "fields": (
                    "electricity",
                    "water",
                    "rent",
                    "waste",
                    "total",
                    "status",
                ),
            },
        ),
        ("Payment Information", {"fields": ("payment_received_date", "total_paid", "remarks")}),
        (
            "Timestamps (Read-only)",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# Register your models here.
admin.site.register(House, HouseAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(PaymentHistory, PaymentHistoryAdmin)
# TenantDocument is managed via TenantInline, but can also be registered directly if needed
admin.site.register(TenantDocument)