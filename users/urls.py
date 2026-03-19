from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('cambiar-clave/', views.change_password_view, name='change_password'),
]
