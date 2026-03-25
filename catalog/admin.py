from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'cost_price', 'sale_price', 'is_active', 'contractor')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')
