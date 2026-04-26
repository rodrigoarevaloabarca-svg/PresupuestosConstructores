from django.urls import path

from . import views

urlpatterns = [
    path('registro/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('cambiar-clave/', views.change_password_view, name='change_password'),
    path('recuperar-clave/', views.password_reset_request_view, name='password_reset_request'),
    path('recuperar-clave/enviado/', views.password_reset_sent_view, name='password_reset_sent'),
    path('resetear-clave/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('resetear-clave/completo/', views.password_reset_complete_view, name='password_reset_complete'),
    # Mercado Pago / Planes
    path('planes/checkout/', views.checkout_start, name='checkout_start'),
    path('planes/exito/', views.checkout_success, name='checkout_success'),
    path('planes/fallo/', views.checkout_failure, name='checkout_failure'),
    # Facturación
    path('mi-cuenta/facturacion/', views.billing_view, name='billing'),
    path('mi-cuenta/facturacion/cancelar/', views.cancel_subscription, name='cancel_subscription'),
    # 2FA
    path('mi-cuenta/2fa/', views.enable_2fa, name='enable_2fa'),
    path('mi-cuenta/2fa/desactivar/', views.disable_2fa, name='disable_2fa'),
    path('mi-cuenta/2fa/verificar/', views.verify_2fa, name='verify_2fa'),
]
