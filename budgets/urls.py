from django.urls import path

from . import views

urlpatterns = [
    path("", views.budget_list, name="budget_list"),
    path("nuevo/", views.budget_create, name="budget_create"),
    path("<int:pk>/", views.budget_detail, name="budget_detail"),
    path("<int:pk>/editar/", views.budget_edit, name="budget_edit"),
    path("<int:pk>/eliminar/", views.budget_delete, name="budget_delete"),
    path("<int:pk>/estado/", views.budget_update_status, name="budget_update_status"),
    path("<int:pk>/pdf/", views.budget_pdf, name="budget_pdf"),
    path("<int:pk>/duplicar/", views.budget_duplicate, name="budget_duplicate"),
    path("<int:pk>/link/", views.budget_generate_link, name="budget_generate_link"),
    path("<int:pk>/link/revocar/", views.budget_revoke_link, name="budget_revoke_link"),
    path("<int:pk>/email/", views.budget_send_email, name="budget_send_email"),
    path("ver/<str:token>/", views.budget_public_view, name="budget_public"),
    path("<int:pk>/whatsapp/", views.budget_send_whatsapp, name="budget_send_whatsapp"),
    path("<int:pk>/facturar/", views.budget_to_invoice_view, name="budget_to_invoice"),
    path("<int:pk>/historial/", views.budget_history, name="budget_history"),
    path("<int:pk>/adjunto/<int:att_pk>/eliminar/", views.budget_delete_attachment, name="budget_delete_attachment"),
    path("plantillas/", views.budget_template_list, name="budget_template_list"),
    path("<int:pk>/guardar-plantilla/", views.budget_save_as_template, name="budget_save_as_template"),
    path("ver/<str:token>/firmar/", views.budget_public_sign, name="budget_public_sign"),
]
