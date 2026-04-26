# Guía Completa — Constructor Express

Constructor Express es un SaaS para contratistas chilenos (gasfiteros, electricistas, constructores, etc.) que permite crear presupuestos en PDF, gestionar clientes y mantener un catálogo de productos. La interfaz está en español chileno y opera con precios en CLP.

**Demo en vivo:** https://rodrigocl.alwaysdata.net
**Credenciales demo:** `demo@constructorexpress.cl` / `Demo1234!`

**Stack tecnológico:** Python 3.12 · Django 5.2 · PostgreSQL (prod) / SQLite (dev) · Celery + Redis · Django REST Framework · Tailwind CSS

---

## Tabla de Contenidos

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación local (desarrollo)](#2-instalación-local-desarrollo)
3. [Variables de entorno](#3-variables-de-entorno)
4. [Instalación con Docker (producción)](#4-instalación-con-docker-producción)
5. [Comandos de gestión](#5-comandos-de-gestión)
6. [Tests](#6-tests)
7. [Uso de la aplicación web](#7-uso-de-la-aplicación-web)
8. [Planes Free vs Pro](#8-planes-free-vs-pro)
9. [API REST](#9-api-rest)
10. [Precios de ferreterías (scraping)](#10-precios-de-ferreterías-scraping)
11. [Arquitectura multi-tenant](#11-arquitectura-multi-tenant)
12. [Seguridad](#12-seguridad)
13. [Estructura del proyecto](#13-estructura-del-proyecto)

---

## 1. Requisitos previos

### Desarrollo local
| Requisito | Versión mínima |
|-----------|---------------|
| Python | 3.12+ |
| pip | 23+ |
| Git | cualquiera |

> SQLite viene incluido con Python. No se necesita instalar ninguna base de datos para desarrollo local.

### Producción (Docker)
| Requisito | Versión mínima |
|-----------|---------------|
| Docker | 24+ |
| Docker Compose | 2.20+ |

### Servicios externos opcionales
| Servicio | Para qué sirve |
|----------|---------------|
| SendGrid | Envío de presupuestos por email |
| Twilio | Envío de presupuestos por WhatsApp |
| MercadoPago | Cobro de suscripciones Pro |
| Sentry | Monitoreo de errores en producción |
| OpenFactura / SII | Emisión de facturas DTE (solo Pro) |

---

## 2. Instalación local (desarrollo)

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd constructor_express

# 2. Crear y activar entorno virtual
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows (cmd)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear tablas (usa SQLite automáticamente)
python manage.py migrate

# 5. Cargar datos de demostración
python manage.py seed_demo

# 6. Iniciar servidor de desarrollo
python manage.py runserver
```

La aplicación queda disponible en **http://localhost:8000**.

Credenciales del usuario demo creado por `seed_demo`:
- Email: `demo@constructorexpress.cl`
- Contraseña: `Demo1234!` <!-- pragma: allowlist secret -->

> **Nota:** Si la variable de entorno `DB_NAME` no está definida, Django usa automáticamente SQLite (`db.sqlite3`). No es necesario configurar nada más para desarrollo.

---

## 3. Variables de entorno

El archivo `.env.example` incluye todas las variables disponibles. Para producción, cópialo a `.env.production`:

```bash
cp .env.example .env.production
# Editar .env.production con los valores reales
```

### Variables obligatorias en producción

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Clave secreta Django (mín. 50 chars, aleatoria) |
| `DEBUG` | `False` | Nunca `True` en producción |
| `ALLOWED_HOSTS` | `tudominio.cl,www.tudominio.cl` | Dominios separados por coma |
| `POSTGRES_DB` | `constructor_express_db` | Nombre de la base de datos |
| `POSTGRES_USER` | `ce_user` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `clave-segura` | Contraseña de PostgreSQL |

### Variables de servicios externos (opcionales)

| Variable | Descripción |
|----------|-------------|
| `SENDGRID_API_KEY` | API key de SendGrid para emails transaccionales |
| `DEFAULT_FROM_EMAIL` | Remitente de emails (ej: `Constructor Express <noreply@tudominio.cl>`) |
| `CELERY_BROKER_URL` | URL de Redis (default: `redis://redis:6379/0`) |
| `MP_ACCESS_TOKEN` | Token de acceso MercadoPago (suscripciones Pro) |
| `MP_PUBLIC_KEY` | Llave pública MercadoPago |
| `MP_WEBHOOK_SECRET` | Secreto HMAC para validar webhooks de MercadoPago |
| `TWILIO_ACCOUNT_SID` | SID de cuenta Twilio para WhatsApp |
| `TWILIO_AUTH_TOKEN` | Token de autenticación Twilio |
| `TWILIO_WHATSAPP_FROM` | Número Twilio WhatsApp (ej: `whatsapp:+14155238886`) |
| `SII_PROVIDER_API_KEY` | API key OpenFactura para DTE/SII (solo Pro) |
| `SII_RUT_EMISOR` | RUT del emisor para facturas (ej: `12345678-9`) |
| `SII_ENV` | `sandbox` o `production` para SII |
| `SENTRY_DSN` | DSN de Sentry para monitoreo de errores |
| `SENTRY_ENV` | Nombre del entorno en Sentry (ej: `production`) |

> **Truco:** En desarrollo nunca es necesario crear `.env.production`. Django detecta que no hay `DB_NAME` y usa SQLite con una `SECRET_KEY` de desarrollo automáticamente.

---

## 4. Instalación con Docker (producción)

Docker Compose levanta cuatro servicios: PostgreSQL, Redis, la aplicación web (Gunicorn) y el worker de Celery.

```bash
# 1. Copiar y configurar variables de entorno
cp .env.example .env.production
# Editar .env.production: SECRET_KEY y POSTGRES_PASSWORD son obligatorios

# 2. Construir imágenes e iniciar servicios
docker-compose up --build

# Primera vez: aplica migraciones y carga datos demo automáticamente
# (solo si DEBUG=True en .env.production)
```

### Servicios del docker-compose

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `db` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Redis 7 (broker Celery) |
| `web` | 8000 | Gunicorn (3 workers) |
| `worker` | — | Celery worker |

El healthcheck del contenedor `web` apunta a `/healthz/`. Si retorna HTTP 200, el servicio está listo.

### Comandos útiles con Docker

```bash
# Ver logs en tiempo real
docker-compose logs -f web

# Aplicar migraciones manualmente
docker-compose exec web python manage.py migrate

# Abrir shell de Django
docker-compose exec web python manage.py shell

# Reiniciar solo el worker de Celery
docker-compose restart worker

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (borra la BD)
docker-compose down -v
```

---

## 5. Comandos de gestión

### Datos de demostración

```bash
# Crear datos demo (crea usuario, clientes, productos y presupuestos de ejemplo)
python manage.py seed_demo

# Eliminar y recrear los datos demo desde cero
python manage.py seed_demo --reset
```

El comando crea:
- Usuario: `demo@constructorexpress.cl` / `Demo1234!` (plan Pro)
- 5 clientes con datos chilenos reales (RUT, teléfono, dirección)
- +100 productos en categorías: gasfitería, electricidad, materiales, herramientas
- Múltiples presupuestos en distintos estados (borrador, enviado, aceptado)

### Scraping de precios de ferreterías

```bash
# Scrapear todos los retailers (Sodimac, Easy, Imperial)
python manage.py scrape_retailers --retailer all

# Scrapear solo un retailer
python manage.py scrape_retailers --retailer sodimac
python manage.py scrape_retailers --retailer easy
python manage.py scrape_retailers --retailer imperial

# Modo dry-run (muestra resultados sin guardar en BD)
python manage.py scrape_retailers --retailer all --dry-run

# Scrapear solo Sodimac (comando dedicado)
python manage.py scrape_sodimac
python manage.py scrape_sodimac --dry-run
```

### Archivos estáticos

```bash
# Necesario antes de correr con DEBUG=False
python manage.py collectstatic --noinput
```

### Migraciones

```bash
# Aplicar migraciones pendientes
python manage.py migrate

# Crear migraciones tras modificar modelos
python manage.py makemigrations
```

---

## 6. Tests

```bash
# Suite completa
python manage.py test budgets clients catalog

# Por app
python manage.py test budgets
python manage.py test clients
python manage.py test catalog

# Clase específica
python manage.py test budgets.tests.BudgetModelTests

# Método específico
python manage.py test budgets.tests.BudgetModelTests.test_total_calculation
```

Los tests usan SQLite en memoria y Celery en modo síncrono (`CELERY_TASK_ALWAYS_EAGER=True`), por lo que no requieren servicios externos.

---

## 7. Uso de la aplicación web

### 7.1 Registro e inicio de sesión

| URL | Descripción |
|-----|-------------|
| `/usuarios/registro/` | Crear cuenta nueva |
| `/usuarios/login/` | Iniciar sesión |
| `/usuarios/logout/` | Cerrar sesión |
| `/usuarios/recuperar-clave/` | Recuperar contraseña por email |

**Autenticación en dos factores (2FA):**
- Activar en `/usuarios/mi-cuenta/2fa/`
- Usa TOTP compatible con Google Authenticator, Authy, etc.
- Al activar: escanear QR o ingresar clave secreta manualmente
- Desactivar en `/usuarios/mi-cuenta/2fa/desactivar/` (requiere código TOTP)

### 7.2 Configurar perfil de contratista

URL: `/usuarios/perfil/`

Completar antes de crear el primer presupuesto. Estos datos aparecen en todos los PDFs generados:

- Nombre de la empresa
- RUT (formato `12.345.678-9`)
- Teléfono
- Dirección
- Logo de la empresa (imagen)
- Color de marca (hexadecimal, ej: `#1a73e8`)
- Días de validez predeterminados para presupuestos
- Términos de pago predeterminados
- Notas predeterminadas

### 7.3 Gestión de clientes

| URL | Descripción |
|-----|-------------|
| `/clientes/` | Listar todos los clientes |
| `/clientes/nuevo/` | Crear nuevo cliente |
| `/clientes/<id>/` | Ver detalle y presupuestos del cliente |
| `/clientes/<id>/editar/` | Editar datos del cliente |
| `/clientes/<id>/eliminar/` | Eliminar cliente |

Campos disponibles: nombre, RUT, email, teléfono, dirección, notas.

> Plan gratuito: máximo **10 clientes**.

### 7.4 Catálogo de productos

| URL | Descripción |
|-----|-------------|
| `/catalogo/` | Listar productos (con filtro por categoría) |
| `/catalogo/nuevo/` | Crear producto |
| `/catalogo/<id>/editar/` | Editar producto |
| `/catalogo/<id>/eliminar/` | Eliminar producto (soft delete) |
| `/catalogo/exportar/` | Descargar catálogo completo como CSV |
| `/catalogo/importar/` | Importar productos desde CSV |

Campos: nombre, descripción, categoría, unidad, precio de costo, precio de venta, SKU.

**Formato del CSV de importación:**
```
Nombre,Descripcion,Categoria,Unidad,Precio Costo,Precio Venta,SKU
Cañería PVC 1/2",Cañería de 6m,gasfiteria,ml,1200,1800,CAN-PVC-12
```
- Separador: coma
- Precios: enteros CLP (sin decimales), acepta punto o coma como separador de miles
- Máximo 5.000 filas por importación

> Plan gratuito: máximo **20 productos**.

### 7.5 Presupuestos — Flujo completo

URL principal: `/presupuestos/`

#### Crear un presupuesto

1. Ir a `/presupuestos/nuevo/`
2. Seleccionar cliente (o crear uno nuevo)
3. Ingresar título y datos generales (validez, IVA, términos de pago)
4. Agregar **items de materiales**: nombre, unidad, cantidad, precio unitario
   - El autocompletado busca en tu catálogo y en Sodimac/Easy/Imperial en tiempo real
5. Agregar **items de mano de obra**: nombre, unidad, cantidad, precio unitario
6. Adjuntar archivos opcionales (fotos, planos, PDFs — hasta 5 archivos, 5 MB c/u)
7. Guardar → el presupuesto queda en estado **borrador**

#### Estados del presupuesto

```
borrador → enviado → aceptado
                  ↘ rechazado
```

| Estado | Descripción |
|--------|-------------|
| `borrador` | En preparación, editable directamente |
| `enviado` | Enviado al cliente, se puede firmar digitalmente |
| `aceptado` | Cliente aceptó (firmó o se marcó manualmente) |
| `rechazado` | Cliente rechazó |

Cambiar estado desde el detalle del presupuesto: botón "Actualizar estado".

#### Acciones disponibles sobre un presupuesto

| Acción | URL | Descripción |
|--------|-----|-------------|
| Ver PDF | `/presupuestos/<id>/pdf/` | Genera y descarga el PDF |
| Enviar por email | `/presupuestos/<id>/email/` | Envía PDF adjunto + link público por email |
| Enviar por WhatsApp | `/presupuestos/<id>/whatsapp/` | Envía link público por WhatsApp |
| Generar link público | `/presupuestos/<id>/link/` | Link para que el cliente vea sin cuenta |
| Revocar link | `/presupuestos/<id>/link/revocar/` | Invalida el link público |
| Duplicar | `/presupuestos/<id>/duplicar/` | Crea una copia en borrador |
| Guardar como plantilla | `/presupuestos/<id>/guardar-plantilla/` | Guarda como plantilla reutilizable |
| Ver historial | `/presupuestos/<id>/historial/` | Registro de todos los cambios |
| Facturar (DTE) | `/presupuestos/<id>/facturar/` | Emitir factura SII (solo Pro) |

#### Firma digital del cliente

Cuando el presupuesto está en estado `enviado`:
1. El contratista genera un link público desde `/presupuestos/<id>/link/`
2. El cliente abre el link sin necesidad de cuenta
3. El cliente ve el detalle del presupuesto y firma en el canvas táctil
4. El sistema guarda la firma como PNG + hash SHA-256 + IP + User-Agent
5. El presupuesto pasa automáticamente a estado `aceptado`

Acceso público: `/presupuestos/ver/<token>/`
Firma pública: `/presupuestos/ver/<token>/firmar/` (rate limit: 3 intentos/hora por IP)

### 7.6 Versionado de presupuestos

Si editas un presupuesto en estado `enviado`, `aceptado` o `rechazado`:
- Se crea automáticamente una nueva versión (v2, v3…) en estado `borrador`
- El presupuesto original se conserva intacto
- Todas las versiones comparten el mismo número de presupuesto
- Las versiones están vinculadas por el campo `parent`

Los presupuestos en `borrador` se editan directamente sin crear versión.

### 7.7 Plantillas de presupuesto

URL: `/presupuestos/plantillas/`

Las plantillas son presupuestos reutilizables sin cliente ni número asignado:

1. Crear un presupuesto con la estructura deseada
2. Ir a "Guardar como plantilla" desde el detalle
3. La plantilla aparece en `/presupuestos/plantillas/`
4. Al usarla: se crea un presupuesto nuevo en borrador con todos los items precargados

> Las plantillas **no cuentan** para el límite mensual del plan gratuito.

### 7.8 Dashboard y analytics

URL: `/dashboard/`

Stats disponibles (cache de 5 minutos):
- Total de clientes activos
- Presupuestos del mes actual
- Ingresos del mes (presupuestos aceptados)
- Tasa de aceptación (%)
- Top productos por margen
- CLV (valor promedio por cliente)

---

## 8. Planes Free vs Pro

| Funcionalidad | Free | Pro |
|---------------|------|-----|
| Presupuestos por mes | 5 | Ilimitados |
| Clientes | 10 | Ilimitados |
| Productos en catálogo | 20 | Ilimitados |
| Plantillas | Ilimitadas | Ilimitadas |
| PDF de presupuestos | ✓ | ✓ |
| Firma digital del cliente | ✓ | ✓ |
| Link público para cliente | ✓ | ✓ |
| Envío por email y WhatsApp | ✓ | ✓ |
| Historial de cambios | ✓ | ✓ |
| Precios de ferreterías | ✓ | ✓ |
| Facturación DTE/SII | ✗ | ✓ |

**Precio Pro:** $9.990 CLP/mes (cobro via MercadoPago)

**Activar Pro:** `/usuarios/planes/checkout/`
**Gestionar suscripción:** `/usuarios/mi-cuenta/facturacion/`
**Cancelar:** `/usuarios/mi-cuenta/facturacion/cancelar/`

Estados de suscripción:
- `active` → suscripción vigente (`is_pro() = True`)
- `pending` → checkout iniciado, pago sin confirmar
- `cancelled` → cancelada
- `past_due` → pago fallido

---

## 9. API REST

La documentación completa está en [docs/api.md](api.md).

**Swagger UI interactivo:** `/api/v1/docs/`
**Schema OpenAPI:** `/api/v1/schema/`

### Autenticación JWT

```bash
# Obtener token de acceso
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@constructorexpress.cl", "password": "Demo1234!"}'

# Respuesta
{
  "access": "eyJ...",   # Token de acceso (válido 1 hora)
  "refresh": "eyJ..."  # Token de renovación (válido 7 días)
}

# Usar el token en requests
curl http://localhost:8000/api/v1/presupuestos/ \
  -H "Authorization: Bearer eyJ..."
```

### Endpoints principales

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/v1/auth/token/` | Obtener JWT |
| POST | `/api/v1/auth/refresh/` | Renovar access token |
| POST | `/api/v1/auth/blacklist/` | Revocar refresh token |
| GET | `/api/v1/stats/` | Stats del dashboard |
| GET | `/api/v1/presupuestos/` | Listar presupuestos |
| GET | `/api/v1/presupuestos/<id>/` | Detalle con items |
| GET/POST | `/api/v1/presupuestos/write/` | CRUD completo con items |
| GET/PUT/PATCH/DELETE | `/api/v1/presupuestos/write/<id>/` | CRUD item específico |
| GET/POST | `/api/v1/clientes/` | Listar/crear clientes |
| GET/PUT/PATCH/DELETE | `/api/v1/clientes/<id>/` | CRUD cliente |
| GET/POST | `/api/v1/productos/` | Listar/crear productos |
| GET/PUT/PATCH/DELETE | `/api/v1/productos/<id>/` | CRUD producto |
| GET | `/api/v1/productos/sugerencias/?q=<term>` | Autocomplete (catálogo + ferreterías) |

### Límites de tasa (throttling)

| Tipo | Límite |
|------|--------|
| Usuario autenticado | 1.000 requests/hora |
| Anónimo | 100 requests/hora |
| Obtención de token | 5 requests/minuto |
| Sugerencias de productos | 60 requests/minuto por usuario |

---

## 10. Precios de ferreterías (scraping)

Constructor Express scrapea automáticamente precios de tres ferreterías chilenas y los muestra en el autocompletado al crear presupuestos.

### Ferreterías integradas

| Ferretería | Tecnología | Frecuencia |
|------------|-----------|-----------|
| Sodimac | JSON API interna | Semanal (dom. 3am) |
| Easy | VTEX API | Semanal (dom. 3am) |
| Imperial | HTML + BeautifulSoup | Semanal (dom. 3am) |

### En la interfaz

Al escribir en el campo de materiales del presupuesto:
1. Primero aparecen resultados de **Mi catálogo** (prioridad)
2. Luego resultados de **Ferreterías** con badge de color y link directo al producto

### Scraping manual

```bash
# Scrapear todos (recomendado para inicializar la BD)
python manage.py scrape_retailers --retailer all

# Ver qué se scrapeará sin guardar
python manage.py scrape_retailers --retailer all --dry-run
```

El scraping automático corre cada domingo a las 3:00 AM via Celery Beat. Los productos no vistos en 60+ días se marcan como inactivos automáticamente.

---

## 11. Arquitectura multi-tenant

Todos los datos están aislados por contratista. No existe ningún dato compartido entre usuarios:

- Cada modelo tiene `contractor = ForeignKey(User)`
- Los números de presupuesto son únicos **por contratista** (no globales)
- Las vistas siempre filtran por `request.user`
- La helper function `get_tenant_object_or_404` previene acceso cruzado

```python
# Patrón correcto en todas las vistas
budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
```

---

## 12. Seguridad

### Autenticación y acceso
- Contraseñas hasheadas con PBKDF2 (Django default)
- 2FA TOTP (Google Authenticator, Authy, etc.)
- Rate limiting en login (5/min), registro (3/h), firma digital (3/h por IP)
- Tokens JWT con expiración corta (1h access, 7d refresh)
- Blacklist de refresh tokens al renovar

### Archivos adjuntos
- Validación por **magic bytes** (no solo extensión): JPEG, PNG, WEBP, PDF
- Límite: 5 archivos por presupuesto, 5 MB por archivo

### Sesiones y cookies
- `SESSION_COOKIE_HTTPONLY = True`
- `CSRF_COOKIE_SAMESITE = 'Lax'`
- `X_FRAME_OPTIONS = 'DENY'`
- Middleware anti-caché en páginas autenticadas (previene back-button post-logout)

### Producción (activado automáticamente si `DEBUG=False`)
- `SECURE_SSL_REDIRECT = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 año)
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`

### Auditoría
- `django-auditlog` registra todos los cambios en `Budget`, `Client` y `Product`
- Ver historial: `/presupuestos/<id>/historial/`

---

## 13. Estructura del proyecto

```
constructor_express/
├── constructor_express/        # Configuración central Django
│   ├── settings.py            # DB, apps, middleware, cache, Celery, JWT, etc.
│   ├── urls.py                # Enrutamiento principal + montaje de API
│   ├── celery.py              # Configuración de Celery
│   └── health.py              # Endpoint /healthz/
│
├── users/                     # Autenticación, perfiles, suscripciones, 2FA
│   ├── models.py              # User, ContractorProfile, Subscription, Payment
│   ├── views.py               # Login, registro, perfil, billing, 2FA
│   ├── plan_guard.py          # Límites del plan gratuito
│   ├── webhooks.py            # Webhook MercadoPago
│   └── management/commands/
│       └── seed_demo.py       # Datos de demostración
│
├── clients/                   # Gestión de clientes
│   └── models.py              # Client
│
├── budgets/                   # Dominio principal — presupuestos
│   ├── models.py              # Budget, BudgetItemMaterial/Labor, BudgetSignature,
│   │                          # BudgetAttachment, BudgetPublicToken
│   ├── views.py               # CRUD, PDF, firma, versioning, templates
│   ├── services/
│   │   ├── versioning.py      # create_new_version(), should_create_version()
│   │   └── whatsapp.py        # Integración Twilio WhatsApp
│   ├── api/                   # Serializers y ViewSet para escritura
│   └── static/budgets/js/
│       └── product_autocomplete.js  # Autocomplete vanilla JS
│
├── catalog/                   # Catálogo de productos + scraping
│   ├── models.py              # Product, RetailerProduct
│   ├── scrapers/              # SodimacScraper, EasyScraper, ImperialScraper
│   ├── tasks.py               # Tarea Celery Beat semanal
│   └── management/commands/
│       └── scrape_retailers.py
│
├── billing/                   # Facturación DTE/SII (scaffolding)
│
├── common/
│   └── tenant.py              # get_tenant_object_or_404()
│
├── docs/
│   ├── api.md                 # Documentación completa de la API REST
│   └── guia-completa.md       # Este archivo
│
├── templates/                 # Templates globales (base.html, landing, partials)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example               # Plantilla de variables de entorno
```

---

*Constructor Express — Todos los derechos reservados*
