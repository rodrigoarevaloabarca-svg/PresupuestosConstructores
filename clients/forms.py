from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'rut', 'phone', 'email', 'address', 'city', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}
