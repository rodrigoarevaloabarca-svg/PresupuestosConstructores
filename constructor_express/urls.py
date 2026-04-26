from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# OpenAPI
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# JWT
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from budgets.api.views import BudgetViewSet

# API imports
from budgets.api_views import BudgetDetailAPIView, BudgetListAPIView, dashboard_stats_api
from catalog.api.views import ProductSuggestionsView
from catalog.api_views import ProductDetailAPIView, ProductListAPIView
from clients.api_views import ClientDetailAPIView, ClientListAPIView
from constructor_express.health import healthz
from users.landing_view import landing_view
from users.serializers import ContractorTokenObtainPairView
from users.webhooks import mercadopago_webhook

urlpatterns = [
    # ── Público ────────────────────────────────────────────────
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),
    path('healthz/', healthz, name='healthz'),

    # ── Aplicación web ─────────────────────────────────────────
    path('usuarios/', include('users.urls')),
    path('clientes/', include('clients.urls')),
    path('catalogo/', include('catalog.urls')),
    path('presupuestos/', include('budgets.urls')),
    path('dashboard/', include('users.dashboard_urls')),

    # ── API REST v1 ────────────────────────────────────────────
    path('api/v1/stats/', dashboard_stats_api, name='api_stats'),
    path('api/v1/presupuestos/', BudgetListAPIView.as_view(), name='api_budget_list'),
    path('api/v1/presupuestos/<int:pk>/', BudgetDetailAPIView.as_view(), name='api_budget_detail'),
    path('api/v1/presupuestos/write/', BudgetViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_budget_write_list'),
    path('api/v1/presupuestos/write/<int:pk>/', BudgetViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api_budget_write_detail'),
    path('api/v1/clientes/', ClientListAPIView.as_view(), name='api_client_list'),
    path('api/v1/clientes/<int:pk>/', ClientDetailAPIView.as_view(), name='api_client_detail'),
    path('api/v1/productos/', ProductListAPIView.as_view(), name='api_product_list'),
    path('api/v1/productos/<int:pk>/', ProductDetailAPIView.as_view(), name='api_product_detail'),
    path('api/v1/productos/sugerencias/', ProductSuggestionsView.as_view(), name='api_product_suggestions'),

    # ── API Auth (JWT) ─────────────────────────────────────────
    path('api/v1/auth/token/', ContractorTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # ── OpenAPI / Docs ─────────────────────────────────────────
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger_ui'),

    # ── Webhooks externos ──────────────────────────────────────
    path('api/webhooks/mercadopago/', mercadopago_webhook, name='webhook_mercadopago'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
