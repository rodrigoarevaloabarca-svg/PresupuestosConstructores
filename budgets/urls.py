from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget_list, name='budget_list'),
    path('nuevo/', views.budget_create, name='budget_create'),
    path('<int:pk>/', views.budget_detail, name='budget_detail'),
    path('<int:pk>/editar/', views.budget_edit, name='budget_edit'),
    path('<int:pk>/eliminar/', views.budget_delete, name='budget_delete'),
    path('<int:pk>/estado/', views.budget_update_status, name='budget_update_status'),
    path('<int:pk>/pdf/', views.budget_pdf, name='budget_pdf'),
    path('<int:pk>/duplicar/', views.budget_duplicate, name='budget_duplicate'),
    path('<int:pk>/link/', views.budget_generate_link, name='budget_generate_link'),
    path('<int:pk>/email/', views.budget_send_email, name='budget_send_email'),
    path('ver/<str:token>/', views.budget_public_view, name='budget_public'),
]
