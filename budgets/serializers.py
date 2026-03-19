from rest_framework import serializers
from .models import Budget, BudgetItemMaterial, BudgetItemLabor
from clients.models import Client


class BudgetItemMaterialSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)

    class Meta:
        model = BudgetItemMaterial
        fields = ['id', 'name', 'unit', 'unit_display', 'quantity', 'unit_price', 'total', 'order']


class BudgetItemLaborSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)

    class Meta:
        model = BudgetItemLabor
        fields = ['id', 'name', 'unit', 'unit_display', 'quantity', 'unit_price', 'total', 'order']


class BudgetListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subtotal_materials = serializers.ReadOnlyField()
    subtotal_labor = serializers.ReadOnlyField()
    total = serializers.ReadOnlyField()

    class Meta:
        model = Budget
        fields = ['id', 'number', 'title', 'client', 'client_name',
                  'status', 'status_display', 'subtotal_materials',
                  'subtotal_labor', 'total', 'created_at', 'valid_until']


class BudgetDetailSerializer(serializers.ModelSerializer):
    material_items = BudgetItemMaterialSerializer(many=True, read_only=True)
    labor_items = BudgetItemLaborSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subtotal_materials = serializers.ReadOnlyField()
    subtotal_labor = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total = serializers.ReadOnlyField()
    valid_until = serializers.ReadOnlyField()

    class Meta:
        model = Budget
        fields = ['id', 'number', 'title', 'client', 'client_name',
                  'status', 'status_display', 'validity_days', 'valid_until',
                  'payment_terms', 'notes', 'tax_percent', 'tax_amount',
                  'subtotal_materials', 'subtotal_labor', 'total',
                  'material_items', 'labor_items', 'created_at', 'updated_at']
