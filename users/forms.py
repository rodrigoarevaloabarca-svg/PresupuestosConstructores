from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from .models import User, ContractorProfile, validate_rut


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    company_name = forms.CharField(label='Nombre de tu empresa')
    rut = forms.CharField(label='RUT de la empresa', help_text='Formato: 12345678-9', validators=[validate_rut])
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


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')

    def get_user(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            return None
        return User.objects.filter(email__iexact=email).first()


class PasswordResetConfirmForm(SetPasswordForm):
    pass


class OTPTokenForm(forms.Form):
    token = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'autocomplete': 'one-time-code', 'inputmode': 'numeric', 'class': 'form-input text-center text-2xl tracking-widest'}),
    )
