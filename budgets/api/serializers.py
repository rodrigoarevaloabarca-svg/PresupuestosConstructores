from django.db import transaction
from rest_framework import serializers

from budgets.models import Budget, BudgetItemLabor, BudgetItemMaterial


class BudgetItemMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItemMaterial
        fields = ["id", "name", "unit", "quantity", "unit_price", "order"]


class BudgetItemLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItemLabor
        fields = ["id", "name", "unit", "quantity", "unit_price", "order"]


class BudgetWriteSerializer(serializers.ModelSerializer):
    material_items = BudgetItemMaterialSerializer(many=True, default=[])
    labor_items = BudgetItemLaborSerializer(many=True, default=[])

    class Meta:
        model = Budget
        fields = [
            "id",
            "client",
            "title",
            "status",
            "validity_days",
            "payment_terms",
            "notes",
            "tax_percent",
            "material_items",
            "labor_items",
        ]
        read_only_fields = ["id"]

    def validate_client(self, client):
        request = self.context["request"]
        if client.contractor != request.user:
            raise serializers.ValidationError("Cliente no pertenece a este contratista.")
        return client

    @transaction.atomic
    def create(self, validated_data):
        material_data = validated_data.pop("material_items", [])
        labor_data = validated_data.pop("labor_items", [])
        validated_data["contractor"] = self.context["request"].user
        budget = Budget.objects.create(**validated_data)
        for item in material_data:
            BudgetItemMaterial.objects.create(budget=budget, **item)
        for item in labor_data:
            BudgetItemLabor.objects.create(budget=budget, **item)
        return budget

    @transaction.atomic
    def update(self, instance, validated_data):
        material_data = validated_data.pop("material_items", None)
        labor_data = validated_data.pop("labor_items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if material_data is not None:
            instance.material_items.all().delete()
            for item in material_data:
                BudgetItemMaterial.objects.create(budget=instance, **item)
        if labor_data is not None:
            instance.labor_items.all().delete()
            for item in labor_data:
                BudgetItemLabor.objects.create(budget=instance, **item)
        return instance


class BudgetReadSerializer(serializers.ModelSerializer):
    material_items = BudgetItemMaterialSerializer(many=True, read_only=True)
    labor_items = BudgetItemLaborSerializer(many=True, read_only=True)
    total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Budget
        fields = [
            "id",
            "number",
            "client",
            "title",
            "status",
            "validity_days",
            "payment_terms",
            "notes",
            "tax_percent",
            "total",
            "material_items",
            "labor_items",
            "created_at",
        ]
