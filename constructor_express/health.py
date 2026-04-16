from django.db import connection
from django.http import JsonResponse


def healthz(request):
    try:
        connection.cursor().execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "db_unavailable"}, status=503)
