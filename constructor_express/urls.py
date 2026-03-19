from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.landing_view import landing_view

# API imports
from budgets.api_views import BudgetListAPIView, BudgetDetailAPIView, dashboard_stats_api
from clients.api_views import ClientListAPIView, ClientDetailAPIView
from catalog.api_views import ProductListAPIView, ProductDetailAPIView

urlpatterns = [
    # ── Público ────────────────────────────────────────────────────
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),

    # ── Aplicación web ─────────────────────────────────────────────
    path('usuarios/', include('users.urls')),
    path('clientes/', include('clients.urls')),
    path('catalogo/', include('catalog.urls')),
    path('presupuestos/', include('budgets.urls')),
    path('dashboard/', include('users.dashboard_urls')),

    # ── API REST v1 ────────────────────────────────────────────────
    path('api/v1/stats/', dashboard_stats_api, name='api_stats'),
    path('api/v1/presupuestos/', BudgetListAPIView.as_view(), name='api_budget_list'),
    path('api/v1/presupuestos/<int:pk>/', BudgetDetailAPIView.as_view(), name='api_budget_detail'),
    path('api/v1/clientes/', ClientListAPIView.as_view(), name='api_client_list'),
    path('api/v1/clientes/<int:pk>/', ClientDetailAPIView.as_view(), name='api_client_detail'),
    path('api/v1/productos/', ProductListAPIView.as_view(), name='api_product_list'),
    path('api/v1/productos/<int:pk>/', ProductDetailAPIView.as_view(), name='api_product_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
