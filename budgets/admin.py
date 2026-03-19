from django.contrib import admin
from .models import Budget, BudgetItemMaterial, BudgetItemLabor

class MaterialInline(admin.TabularInline):
    model = BudgetItemMaterial
    extra = 0

class LaborInline(admin.TabularInline):
    model = BudgetItemLabor
    extra = 0

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'client', 'status', 'total', 'created_at']
    list_filter = ['status']
    inlines = [MaterialInline, LaborInline]
    readonly_fields = ['created_at', 'updated_at']
