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
]
