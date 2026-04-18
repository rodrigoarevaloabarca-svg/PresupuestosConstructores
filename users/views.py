import logging

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
    OTPTokenForm,
)
from .models import ContractorProfile, User, Subscription

logger = logging.getLogger('users.auth')


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
            from django_otp.plugins.otp_totp.models import TOTPDevice
            if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                request.session['_2fa_pending_uid'] = user.pk
                return redirect('verify_2fa')
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


# ─── Mercado Pago checkout ────────────────────────────────────────────────────

@login_required
def checkout_start(request):
    if not settings.MP_ACCESS_TOKEN:
        messages.error(request, 'Pagos no configurados. Contacta soporte.')
        return redirect('dashboard')
    try:
        import mercadopago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        back_url = request.build_absolute_uri('/usuarios/planes/exito/')
        preapproval_data = {
            'reason': 'Constructor Express — Plan Pro mensual',
            'auto_recurring': {
                'frequency': 1,
                'frequency_type': 'months',
                'transaction_amount': 9990,
                'currency_id': 'CLP',
            },
            'back_url': back_url,
            'payer_email': request.user.email,
            'status': 'pending',
        }
        result = sdk.preapproval().create(preapproval_data)
        if result['status'] in (200, 201):
            info = result['response']
            sub, _ = Subscription.objects.get_or_create(
                contractor=request.user,
                mp_preapproval_id=info['id'],
                defaults={'amount_clp': 9990, 'status': 'pending'},
            )
            return redirect(info['init_point'])
        messages.error(request, 'Error al crear el checkout. Intenta de nuevo.')
    except Exception as e:
        logger.error('checkout_start error para %s: %s', request.user.email, e)
        messages.error(request, 'Error inesperado. Intenta de nuevo.')
    return redirect('dashboard')


@login_required
def checkout_success(request):
    return render(request, 'users/checkout_success.html')


@login_required
def checkout_failure(request):
    return render(request, 'users/checkout_failure.html')


# ─── Facturación ─────────────────────────────────────────────────────────────

@login_required
def billing_view(request):
    subscription = (
        Subscription.objects.filter(contractor=request.user, status='active')
        .order_by('-created_at').first()
    )
    payments = []
    if subscription:
        payments = list(subscription.payments.order_by('-paid_at')[:12])
    return render(request, 'users/billing.html', {
        'subscription': subscription,
        'payments': payments,
    })


@login_required
def cancel_subscription(request):
    if request.method != 'POST':
        return redirect('billing')
    sub = Subscription.objects.filter(contractor=request.user, status='active').first()
    if not sub:
        messages.warning(request, 'No tienes una suscripción activa.')
        return redirect('billing')
    try:
        import mercadopago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        sdk.preapproval().update(sub.mp_preapproval_id, {'status': 'cancelled'})
        sub.status = 'cancelled'
        sub.save()
        messages.success(
            request,
            f'Suscripción cancelada. Tu plan Pro sigue activo hasta '
            f'{sub.next_billing_date.strftime("%d/%m/%Y") if sub.next_billing_date else "fin del período"}.'
        )
    except Exception as e:
        logger.error('cancel_subscription error: %s', e)
        messages.error(request, 'Error al cancelar. Contacta soporte.')
    return redirect('billing')


# ─── 2FA / TOTP ──────────────────────────────────────────────────────────────

@login_required
def enable_2fa(request):
    from django_otp.plugins.otp_totp.models import TOTPDevice
    import qrcode
    import qrcode.image.svg
    import io

    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if device:
        messages.info(request, '2FA ya está activado en tu cuenta.')
        return redirect('profile')

    pending = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
    if not pending:
        pending = TOTPDevice.objects.create(user=request.user, name='default', confirmed=False)

    if request.method == 'POST':
        form = OTPTokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            if pending.verify_token(token):
                pending.confirmed = True
                pending.save()
                messages.success(request, '2FA activado correctamente.')
                return redirect('profile')
            messages.error(request, 'Código incorrecto. Intenta de nuevo.')
    else:
        form = OTPTokenForm()

    qr_url = pending.config_url
    img = qrcode.make(qr_url, image_factory=qrcode.image.svg.SvgImage)
    buf = io.BytesIO()
    img.save(buf)
    qr_svg = buf.getvalue().decode('utf-8')

    return render(request, 'users/2fa_setup.html', {'form': form, 'qr_svg': qr_svg, 'device': pending})


@login_required
def disable_2fa(request):
    from django_otp.plugins.otp_totp.models import TOTPDevice
    if request.method == 'POST':
        form = OTPTokenForm(request.POST)
        if form.is_valid():
            device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
            if device and device.verify_token(form.cleaned_data['token']):
                TOTPDevice.objects.filter(user=request.user).delete()
                messages.success(request, '2FA desactivado.')
                return redirect('profile')
            messages.error(request, 'Código incorrecto.')
    else:
        form = OTPTokenForm()
    return render(request, 'users/2fa_disable.html', {'form': form})


def verify_2fa(request):
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django.contrib.auth import SESSION_KEY
    if SESSION_KEY in request.session:
        return redirect('dashboard')

    pending_uid = request.session.get('_2fa_pending_uid')
    if not pending_uid:
        return redirect('login')

    if request.method == 'POST':
        form = OTPTokenForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(pk=pending_uid)
            except User.DoesNotExist:
                return redirect('login')
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if device and device.verify_token(form.cleaned_data['token']):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['_2fa_pending_uid']
                return redirect('dashboard')
            messages.error(request, 'Código incorrecto.')
    else:
        form = OTPTokenForm()
    return render(request, 'users/2fa_verify.html', {'form': form})
