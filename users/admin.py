from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ContractorProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'plan', 'is_active']
    list_filter = ['plan', 'is_active']
    fieldsets = UserAdmin.fieldsets + (('Plan', {'fields': ('plan', 'plan_expires_at')}),)

@admin.register(ContractorProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'rut', 'rubro', 'user']
