from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ContractorProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    company_name = forms.CharField(label='Nombre de tu empresa')
    rut = forms.CharField(label='RUT de la empresa', help_text='Formato: 12345678-9')
    phone = forms.CharField(label='Teléfono de contacto')
    rubro = forms.ChoiceField(label='Rubro principal', choices=ContractorProfile._meta.get_field('rubro').choices)

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            ContractorProfile.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                rut=self.cleaned_data['rut'],
                phone=self.cleaned_data['phone'],
                rubro=self.cleaned_data['rubro'],
            )
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Correo electrónico')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = ContractorProfile
        fields = ['company_name', 'rut', 'rubro', 'phone', 'address', 'city',
                  'logo', 'brand_color', 'website', 'budget_validity_days',
                  'payment_terms', 'notes_template']
        widgets = {
            'brand_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 cursor-pointer rounded'}),
            'payment_terms': forms.Textarea(attrs={'rows': 3}),
            'notes_template': forms.Textarea(attrs={'rows': 3}),
        }
