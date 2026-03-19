from django.contrib import admin
from .models import Client
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'rut', 'phone', 'city', 'contractor']
    search_fields = ['name', 'rut']
