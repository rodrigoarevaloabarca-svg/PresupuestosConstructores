from django.urls import path
from . import dashboard_views, reports_view, search_view

urlpatterns = [
    path('', dashboard_views.dashboard_view, name='dashboard'),
    path('reportes/', reports_view.reports_view, name='reports'),
    path('buscar/', search_view.global_search, name='global_search'),
]
