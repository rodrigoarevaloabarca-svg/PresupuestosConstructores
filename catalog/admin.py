from django.contrib import admin
from .models import Product, RetailerProduct


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'cost_price', 'sale_price', 'is_active', 'contractor')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RetailerProduct)
class RetailerProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'retailer', 'price_clp', 'sku', 'is_active', 'last_scraped')
    list_filter = ('retailer', 'is_active')
    search_fields = ('name', 'sku')
    readonly_fields = ('last_scraped',)
