from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django_ratelimit.decorators import ratelimit
from .email_utils import send_password_reset_email
from .forms import (
    RegisterForm,
    LoginForm,
    ProfileForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
)
from .models import ContractorProfile, User


@ratelimit(key='ip', rate='3/h', block=True, method='POST')
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido a Constructor Express! Tu cuenta ha sido creada.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


@ratelimit(key='ip', rate='5/m', block=True, method='POST')
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        request.session.flush()
        response = redirect('landing')
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response
    # GET: redirigir al login si no está autenticado, al dashboard si lo está
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = ContractorProfile.objects.get_or_create(
        user=request.user,
        defaults={'company_name': request.user.email, 'rut': '00000000-0', 'phone': ''}
    )
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'users/profile.html', {'form': form, 'profile': profile})


from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '✅ Contraseña actualizada correctamente.')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})


@ratelimit(key='ip', rate='3/h', block=True, method='POST')
def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None and user.is_active:
                send_password_reset_email(user, request)
            else:
                # Dummy work to match timing — prevent user enumeration
                import hashlib
                hashlib.pbkdf2_hmac('sha256', b'dummy', b'salt', 260000)
            return redirect('password_reset_sent')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_sent_view(request):
    return render(request, 'users/password_reset_sent.html')


def _get_user_from_uidb64(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None


def password_reset_confirm_view(request, uidb64, token):
    user = _get_user_from_uidb64(uidb64)
    token_generator = PasswordResetTokenGenerator()
    if user is None or not token_generator.check_token(user, token):
        return render(request, 'users/password_reset_invalid.html', status=400)

    if request.method == 'POST':
        form = PasswordResetConfirmForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('password_reset_complete')
    else:
        form = PasswordResetConfirmForm(user)
    return render(request, 'users/password_reset_confirm.html', {'form': form})


def password_reset_complete_view(request):
    return render(request, 'users/password_reset_complete.html')
