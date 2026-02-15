from django import forms

from .models import PaymentHistory, Tenant, TenantDocument, Room


class PaymentHistoryForm(forms.ModelForm):
    class Meta:
        model = PaymentHistory
        fields = [
            "billing_month",
            "current_units",
            "payment_received_date",
            "total_paid",
            "remarks",
        ]
        widgets = {
            "billing_month": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                }
            ),
            "current_units": forms.NumberInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                }
            ),
            "payment_received_date": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                }
            ),
            "total_paid": forms.NumberInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm",
                    "step": "0.01",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm",
                    "rows": 3,
                }
            ),
        }


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "name",
            "contact",
            "email",
            "move_in_date",
            "rent_price",
            "electricity_price_per_unit",
            "water_price",
            "waste_price",
            "initial_unit",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "contact": forms.TextInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "move_in_date": forms.DateInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm",
                    "type": "date",
                }
            ),
            "rent_price": forms.NumberInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "electricity_price_per_unit": forms.NumberInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "water_price": forms.NumberInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "waste_price": forms.NumberInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
            "initial_unit": forms.NumberInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            ),
        }


class TenantDocumentForm(forms.ModelForm):
    class Meta:
        model = TenantDocument
        fields = ["name", "document"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                }
            ),
            "document": forms.ClearableFileInput(
                attrs={"class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"}
            )
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_name", "room_number"]
        widgets = {
            "room_name": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm",
                    "placeholder": "e.g. Master Bedroom (optional)"
                }
            ),
            "room_number": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm",
                    "placeholder": "e.g. 101, A1, Suite 1"
                }
            ),
        }
