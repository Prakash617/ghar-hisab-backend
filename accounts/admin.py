from django.contrib import admin
from .models import EmailSettings


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ("EMAIL_HOST_USER", "EMAIL_HOST", "EMAIL_PORT")
