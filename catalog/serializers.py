from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    margin = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'category_display',
                  'unit', 'unit_display', 'cost_price', 'sale_price', 'margin',
                  'sku', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'margin']
