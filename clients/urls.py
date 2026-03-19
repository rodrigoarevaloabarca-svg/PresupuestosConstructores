from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('nuevo/', views.client_create, name='client_create'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/editar/', views.client_edit, name='client_edit'),
    path('<int:pk>/eliminar/', views.client_delete, name='client_delete'),
]
