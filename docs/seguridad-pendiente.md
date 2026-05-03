# Revisión de Seguridad — Pendientes de Implementación

Auditoría realizada: 2026-05-02

---

## 🔴 Alta — Corregir antes del próximo deploy

### 1. IDOR — llamadas incorrectas a `get_tenant_object_or_404`

**Archivos:** `budgets/views.py` (~línea 444 y ~línea 538)
**Funciones:** `budget_send_whatsapp()` y `budget_to_invoice_view()`

**Problema:**
Se llama como:
```python
budget = get_tenant_object_or_404(Budget, pk=pk, user=request.user)
```
La firma correcta es `(model, request, **kwargs)`. Al pasar `user=request.user` como kwarg en lugar de `request` como segundo argumento posicional, la protección multi-tenant no se aplica y la función lanza `TypeError` al ejecutarse.

**Corrección:**
```python
budget = get_tenant_object_or_404(Budget, request, pk=pk)
```

---

### 2. Rate limiting en firma digital — bypasseable por IP compartida

**Archivo:** `budgets/views.py` (~línea 466, `budget_public_sign()`)

**Problema:**
El rate limit de `3/h` se aplica por IP. En redes corporativas o NAT, múltiples usuarios comparten la misma IP pública, lo que permite que un atacante agote el rate limit de todos los usuarios de esa red.

**Mejora sugerida:**
Complementar con rate limit por token además de por IP:
```python
@ratelimit(key="ip", rate="3/h", block=True)
@ratelimit(key="get:token", rate="5/h", block=True)
def budget_public_sign(request, token):
    ...
```

---

## 🟡 Media

### 3. Validación de adjuntos — ataque polyglot

**Archivo:** `budgets/views.py`, función `_save_attachments()`

**Problema:**
Se validan magic bytes pero no se cruza con la extensión del archivo. Un archivo llamado `exploit.php` con magic bytes de JPG pasa la validación de contenido. Si el servidor web está configurado para ejecutar scripts por extensión, podría ejecutarse.

**Corrección:**
Agregar validación de extensión y cruzarla con el tipo detectado por magic bytes:
```python
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.pdf', '.webp'}

ext = os.path.splitext(f.name)[1].lower()
if ext not in ALLOWED_EXTS:
    continue
```

---

### 4. `_sanitize_logo()` — excepción genérica oculta errores reales

**Archivo:** `users/models.py`, función `_sanitize_logo()`

**Problema:**
El bloque `except Exception` captura todo sin distinción, incluyendo errores de disco, memoria o permisos, retornando silenciosamente sin sanitizar la imagen.

**Corrección:**
Re-lanzar como `ValidationError` para errores de imagen, pero dejar pasar errores de sistema:
```python
except (OSError, SyntaxError) as exc:
    raise ValidationError("El archivo no es una imagen válida.") from exc
```

---

### 5. Webhook MercadoPago — sin rate limiting y sin validación de `data.id`

**Archivo:** `users/webhooks.py`

**Problema:**
- No hay rate limiting en el endpoint del webhook, exponiéndolo a flood de requests.
- El parámetro `data.id` (`query_id`) no se valida como numérico antes de usarlo.

**Corrección:**
```python
@ratelimit(key="ip", rate="100/h", block=True)
def mercadopago_webhook(request):
    ...
    query_id = request.GET.get("data.id", "").strip()
    if not query_id or not query_id.isdigit():
        return JsonResponse({"error": "id inválido"}, status=400)
```

---

### 6. Error de generación PDF expuesto al usuario

**Archivo:** `budgets/views.py`, función `budget_pdf()`

**Problema:**
El mensaje de excepción de WeasyPrint se muestra directamente al usuario:
```python
messages.error(request, f"Error al generar el PDF: {e}")
```
Esto puede filtrar rutas del sistema, versiones de librerías u otra información técnica.

**Corrección:**
```python
except Exception as e:
    logger.error("PDF generation failed for budget %s: %s", pk, e)
    messages.error(request, "Error al generar el PDF. Por favor intenta de nuevo.")
    return redirect("budget_detail", pk=pk)
```

---

## 🟢 Baja

### 7. `ALLOWED_ATTACHMENT_TYPES` definida pero no usada

**Archivo:** `budgets/views.py`

La constante `ALLOWED_ATTACHMENT_TYPES` está definida pero los magic bytes están hardcodeados inline en la función. Refactorizar para usar la constante y evitar duplicación.

---

### 8. Feedback silencioso al exceder 5 adjuntos

**Archivo:** `budgets/views.py`, función `_save_attachments()`

Si el usuario intenta subir más de 5 archivos, los extras se descartan sin aviso. Agregar un mensaje de advertencia al usuario.

---

### 9. Kwarg `user=request.user` sin efecto (relacionado con punto #1)

**Archivo:** `budgets/views.py` (~líneas 444 y 538)

Limpiar el kwarg `user=request.user` después de corregir la llamada a `get_tenant_object_or_404`.

---

## ✅ Confirmado seguro — sin acción requerida

| Area | Detalle |
|------|---------|
| Multi-tenancy | Todas las querysets y vistas filtran por `contractor=request.user` |
| Token público | `secrets.token_urlsafe(32)`, expira 30 días, revocación, valida `is_revoked` + `expires_at` |
| Firma digital | Valida estado `enviado`, evita firmas múltiples, guarda IP + User-Agent + SHA-256 |
| CSRF | Activo en todas las vistas; webhook usa HMAC con `hmac.compare_digest()` |
| 2FA/TOTP | Implementado con `django-otp`, rate limit en login/registro/firma |
| Headers HTTP | `X-Frame-Options: DENY`, `nosniff`, HSTS en producción, cookies `Secure + SameSite` |
| Logo upload | Extensión + magic bytes + 500 KB + min 50 px + re-encodeo Pillow (elimina EXIF) |
| API REST | `IsAuthenticated` en todas las vistas, querysets filtradas por contractor |
| Inyección SQL | Sin `.raw()`, `.extra()`, `eval()`, `exec()` — todo ORM puro |
| Cookies | `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY`, `SameSite=Lax`, `Secure` en prod |
| `SECRET_KEY` | Requerido en producción, lanza `ImproperlyConfigured` si falta |
| Cache autenticado | `NoCacheAuthMiddleware` agrega `Cache-Control: no-store` a páginas autenticadas |

---

## Resumen

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 Alta   | 2        | Pendiente |
| 🟡 Media  | 4        | Pendiente |
| 🟢 Baja   | 3        | Pendiente |
| ✅ OK     | 13 areas | Sin cambios |
