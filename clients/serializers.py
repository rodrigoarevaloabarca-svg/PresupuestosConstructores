from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    budget_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'name', 'rut', 'phone', 'email', 'address', 'city', 'notes',
                  'budget_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'budget_count']

    def get_budget_count(self, obj):
        return obj.budgets.count()
