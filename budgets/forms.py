from django import forms
from .models import Budget
from clients.models import Client


class BudgetForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['client'].queryset = Client.objects.filter(contractor=user)

    class Meta:
        model = Budget
        fields = ['client', 'title', 'validity_days', 'tax_percent', 'payment_terms', 'notes']
        widgets = {
            'payment_terms': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
