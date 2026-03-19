from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('nuevo/', views.product_create, name='product_create'),
    path('<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('<int:pk>/eliminar/', views.product_delete, name='product_delete'),
    path('api/buscar/', views.product_search_api, name='product_search_api'),
    path('exportar/', views.product_export_csv, name='product_export_csv'),
    path('importar/', views.product_import_csv, name='product_import_csv'),
]
