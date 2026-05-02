# Guia Completa — Constructor Express

Constructor Express es un SaaS para contratistas chilenos (gasfiteros, electricistas, constructores, pintores, etc.) que permite crear presupuestos profesionales en PDF, gestionar clientes, mantener un catalogo de productos con precios de ferreterias en tiempo real, y recibir la aceptacion del cliente con firma digital.

**Demo en vivo:** https://rodrigocl.alwaysdata.net
**Credenciales demo:** `demo@constructorexpress.cl` / `Demo1234!`

**Stack:** Python 3.12 · Django 5.2 · PostgreSQL (produccion) / SQLite (desarrollo) · Celery + Redis · Django REST Framework · Tailwind CSS

---

## Tabla de contenidos

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalacion local (desarrollo)](#2-instalacion-local-desarrollo)
3. [Variables de entorno](#3-variables-de-entorno)
4. [Docker (produccion)](#4-docker-produccion)
5. [Comandos de gestion](#5-comandos-de-gestion)
6. [Tests](#6-tests)
7. [Uso de la aplicacion web](#7-uso-de-la-aplicacion-web)
8. [Planes Free vs Pro](#8-planes-free-vs-pro)
9. [API REST](#9-api-rest)
10. [Precios de ferreterias (scraping)](#10-precios-de-ferreterias-scraping)
11. [Arquitectura multi-tenant](#11-arquitectura-multi-tenant)
12. [Seguridad](#12-seguridad)
13. [Estructura del proyecto](#13-estructura-del-proyecto)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Requisitos previos

### Desarrollo local

| Requisito | Version minima |
|-----------|---------------|
| Python | 3.12+ |
| pip | 23+ |
| Git | cualquiera |

SQLite viene incluido con Python. No es necesario instalar ninguna base de datos para desarrollo local.

### Produccion (Docker)

| Requisito | Version minima |
|-----------|---------------|
| Docker | 24+ |
| Docker Compose | 2.20+ |

### Servicios externos opcionales

| Servicio | Para que sirve |
|----------|---------------|
| SendGrid | Envio de presupuestos por email |
| Twilio | Envio de presupuestos por WhatsApp |
| MercadoPago | Cobro de suscripciones Pro ($9.990 CLP/mes) |
| Sentry | Monitoreo de errores en produccion |
| OpenFactura / SII | Emision de facturas DTE (solo Pro) |

---

## 2. Instalacion local (desarrollo)

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd constructor_express

# 2. Crear y activar entorno virtual
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear tablas (SQLite automatico — no se requiere configuracion)
python manage.py migrate

# 5. Cargar datos de demostracion
python manage.py seed_demo

# 6. Iniciar servidor de desarrollo
python manage.py runserver
```

La aplicacion queda disponible en **http://localhost:8000**.

Credenciales del usuario demo:
- Email: `demo@constructorexpress.cl` # pragma: allowlist secret
- Contrasena: `Demo1234!` # pragma: allowlist secret

> Si `DB_NAME` no esta definida como variable de entorno, Django usa SQLite automaticamente (`db.sqlite3`). No es necesario crear ningun archivo `.env` para desarrollo local.

### Instalacion de dependencias de desarrollo (opcional)

Para ejecutar los tests con pytest, lint y pre-commit hooks:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

---

## 3. Variables de entorno

El archivo `.env.example` lista todas las variables disponibles. Para produccion, copialo a `.env_producion` (atencion: sin la `c` final — nombre requerido por el cargador de settings):

```bash
cp .env.example .env_producion
# Editar .env_producion con los valores reales
```

### Variables obligatorias en produccion

| Variable | Ejemplo | Descripcion |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-abc123...` | Clave secreta Django (minimo 50 chars, generada aleatoriamente) |
| `DEBUG` | `False` | Nunca `True` en produccion |
| `ALLOWED_HOSTS` | `tudominio.cl,www.tudominio.cl` | Dominios separados por coma |
| `POSTGRES_DB` | `constructor_express_db` | Nombre de la base de datos |
| `POSTGRES_USER` | `ce_user` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `clave-segura` | Contrasena de PostgreSQL |

### Variables de servicios externos (opcionales)

| Variable | Descripcion |
|----------|-------------|
| `SENDGRID_API_KEY` | API key de SendGrid para emails transaccionales |
| `DEFAULT_FROM_EMAIL` | Remitente de emails (ej: `Constructor Express <noreply@tudominio.cl>`) |
| `CELERY_BROKER_URL` | URL de Redis (default en Docker: `redis://redis:6379/0`) |
| `MP_ACCESS_TOKEN` | Token de acceso MercadoPago (suscripciones Pro) |
| `MP_PUBLIC_KEY` | Llave publica MercadoPago (checkout en browser) |
| `MP_WEBHOOK_SECRET` | Secreto HMAC para validar webhooks de MercadoPago |
| `TWILIO_ACCOUNT_SID` | SID de cuenta Twilio para WhatsApp |
| `TWILIO_AUTH_TOKEN` | Token de autenticacion Twilio |
| `TWILIO_WHATSAPP_FROM` | Numero Twilio WhatsApp (ej: `whatsapp:+14155238886`) |
| `SII_PROVIDER_API_KEY` | API key OpenFactura para DTE/SII (solo Pro) |
| `SII_RUT_EMISOR` | RUT del emisor para facturas (ej: `12345678-9`) |
| `SII_ENV` | `sandbox` o `production` para SII |
| `SENTRY_DSN` | DSN de Sentry para monitoreo de errores |
| `SENTRY_ENV` | Nombre del entorno en Sentry (ej: `production`) |

> **Detalle de la deteccion automatica de BD:** Si `DB_NAME` no esta definida, Django usa SQLite con `db.sqlite3`. Si esta definida, usa PostgreSQL con las variables `POSTGRES_*`. No hay ninguna otra configuracion necesaria.

---

## 4. Docker (produccion)

Docker Compose levanta cuatro servicios: PostgreSQL 15, Redis 7, la aplicacion web (Gunicorn) y el worker de Celery.

```bash
# 1. Configurar variables de entorno
cp .env.example .env_producion
# Editar: SECRET_KEY y POSTGRES_PASSWORD son obligatorios

# 2. Construir e iniciar
docker-compose up --build

# En la primera ejecucion, aplica migraciones automaticamente.
# Si DEBUG=True, tambien carga los datos de demostracion.
```

### Servicios

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| `db` | 5432 | PostgreSQL 15 (healthcheck: `pg_isready`) |
| `redis` | 6379 | Redis 7, broker de Celery (healthcheck: `redis-cli ping`) |
| `web` | 8000 | Gunicorn (3 workers, healthcheck: `GET /healthz/`) |
| `worker` | — | Celery worker + Beat (scrapers semanal) |

### Comandos utiles con Docker

```bash
# Logs en tiempo real
docker-compose logs -f web
docker-compose logs -f worker

# Aplicar migraciones manualmente
docker-compose exec web python manage.py migrate

# Abrir shell de Django
docker-compose exec web python manage.py shell

# Correr scraping manual
docker-compose exec web python manage.py scrape_retailers --retailer all

# Reiniciar solo el worker de Celery
docker-compose restart worker

# Detener todos los servicios
docker-compose down

# Detener y eliminar volumenes (borra la BD completa)
docker-compose down -v
```

---

## 5. Comandos de gestion

### Datos de demostracion

```bash
# Crea usuario, clientes, productos y presupuestos de ejemplo
python manage.py seed_demo

# Elimina y recrea los datos demo desde cero
python manage.py seed_demo --reset
```

El comando crea:
- Usuario `demo@constructorexpress.cl` con plan Pro
- 5 clientes con datos chilenos reales (RUT, telefono, direccion)
- Mas de 100 productos en categorias: gasfiteria, electricidad, materiales, herramientas
- Multiples presupuestos en distintos estados (borrador, enviado, aceptado)

### Scraping de precios de ferreterias

```bash
# Todos los retailers (recomendado para inicializar la BD)
python manage.py scrape_retailers --retailer all

# Un retailer especifico
python manage.py scrape_retailers --retailer sodimac
python manage.py scrape_retailers --retailer easy
python manage.py scrape_retailers --retailer imperial

# Ver resultados sin guardar en BD
python manage.py scrape_retailers --retailer all --dry-run

# Comando dedicado para Sodimac
python manage.py scrape_sodimac
python manage.py scrape_sodimac --dry-run
```

### Otros comandos

```bash
# Aplicar migraciones pendientes
python manage.py migrate

# Crear migraciones tras modificar modelos
python manage.py makemigrations

# Archivos estaticos (necesario antes de DEBUG=False)
python manage.py collectstatic --noinput
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

# Clase especifica
python manage.py test budgets.tests.BudgetModelTests

# Metodo especifico
python manage.py test budgets.tests.BudgetModelTests.test_total_calculation

# Con pytest y cobertura
pytest --cov --cov-fail-under=60
```

Los tests usan SQLite en memoria y Celery en modo sincrono (`CELERY_TASK_ALWAYS_EAGER=True`). No requieren servicios externos.

**Cobertura por app (aprox. 1.150 lineas de tests en total):**

| App | Que cubre |
|-----|-----------|
| `users` | Auth, 2FA, planes, webhooks MercadoPago |
| `clients` | CRUD clientes, validacion RUT |
| `catalog` | CRUD productos, scrapers, endpoint de sugerencias |
| `budgets` | Totales de presupuesto, versionado, firma digital, items |

---

## 7. Uso de la aplicacion web

### 7.1 Registro e inicio de sesion

| URL | Descripcion |
|-----|-------------|
| `/usuarios/registro/` | Crear cuenta nueva |
| `/usuarios/login/` | Iniciar sesion |
| `/usuarios/logout/` | Cerrar sesion |
| `/usuarios/recuperar-clave/` | Recuperar contrasena por email |

**Autenticacion en dos factores (2FA):**

- Activar: `/usuarios/mi-cuenta/2fa/` — escanear QR con Google Authenticator o Authy
- Verificar: al iniciar sesion, si 2FA esta activo, se pide el codigo TOTP de 6 digitos
- Desactivar: `/usuarios/mi-cuenta/2fa/desactivar/` (requiere codigo TOTP)

---

### 7.2 Configurar perfil de contratista

URL: `/usuarios/perfil/`

Completar antes de crear el primer presupuesto. Estos datos aparecen en todos los PDFs generados:

| Campo | Descripcion |
|-------|-------------|
| Nombre de la empresa | Aparece en cabecera del PDF |
| RUT | Formato `12.345.678-9` |
| Rubro | Gasfiteria, electricidad, construccion, etc. |
| Telefono / Direccion | Datos de contacto en el PDF |
| Logo | Imagen de la empresa (JPG, PNG, WEBP) |
| Color de marca | Hexadecimal (ej: `#1a73e8`) — usado en cabecera del PDF |
| Dias de validez predeterminados | Default para presupuestos nuevos |
| Terminos de pago predeterminados | Texto libre, ej: "50% anticipo, saldo a la entrega" |

---

### 7.3 Gestion de clientes

| URL | Descripcion |
|-----|-------------|
| `/clientes/` | Listar clientes (20 por pagina) |
| `/clientes/nuevo/` | Crear nuevo cliente |
| `/clientes/<id>/` | Ver detalle y presupuestos del cliente |
| `/clientes/<id>/editar/` | Editar datos del cliente |
| `/clientes/<id>/eliminar/` | Eliminar cliente |

Campos: nombre, RUT, email, telefono, direccion, ciudad, notas.

> Plan gratuito: maximo **10 clientes**.

---

### 7.4 Catalogo de productos

| URL | Descripcion |
|-----|-------------|
| `/catalogo/` | Listar productos (filtrable por categoria) |
| `/catalogo/nuevo/` | Crear producto |
| `/catalogo/<id>/editar/` | Editar producto |
| `/catalogo/<id>/eliminar/` | Eliminar producto |
| `/catalogo/exportar/` | Descargar catalogo completo como CSV |
| `/catalogo/importar/` | Importar productos desde CSV |

Campos: nombre, descripcion, categoria, unidad, precio de costo, precio de venta, SKU.

**Formato CSV de importacion:**
```
Nombre,Descripcion,Categoria,Unidad,Precio Costo,Precio Venta,SKU
Caneria PVC 1/2",Caneria de 6m,gasfiteria,ml,1200,1800,CAN-PVC-12
Cable 2.5mm THHN,,electricidad,ml,650,890,CAB-THHN-25
```

- Separador: coma
- Precios: enteros CLP (sin decimales), acepta punto como separador de miles
- Maximo 5.000 filas por importacion

> Plan gratuito: maximo **20 productos**.

---

### 7.5 Presupuestos — Flujo completo

URL principal: `/presupuestos/`

#### Crear un presupuesto

1. Ir a `/presupuestos/nuevo/`
2. Seleccionar cliente (o crear uno nuevo desde el formulario)
3. Ingresar titulo y datos generales: validez, IVA, terminos de pago, notas
4. Agregar **items de materiales**: nombre, unidad, cantidad, precio unitario
   - El autocompletado busca en tu catalogo y en Sodimac/Easy/Imperial en tiempo real (minimo 3 caracteres)
   - Al seleccionar una sugerencia, rellena nombre y precio automaticamente
5. Agregar **items de mano de obra**: nombre, unidad, cantidad, precio unitario
6. Adjuntar archivos opcionales: fotos, planos, PDFs (maximo 5 archivos, 5 MB c/u)
7. Guardar → el presupuesto queda en estado **borrador**

#### Estados del presupuesto

```
borrador ──► enviado ──► aceptado
                    └──► rechazado
```

| Estado | Descripcion | Edicion |
|--------|-------------|---------|
| `borrador` | En preparacion | Edicion directa |
| `enviado` | Compartido con el cliente | Edicion crea version nueva |
| `aceptado` | Cliente acepto (firmo o se marco manualmente) | Edicion crea version nueva |
| `rechazado` | Cliente rechazo | Edicion crea version nueva |

#### Acciones sobre un presupuesto

| Accion | URL | Descripcion |
|--------|-----|-------------|
| Ver PDF | `/presupuestos/<id>/pdf/` | Genera y descarga el PDF |
| Enviar por email | `/presupuestos/<id>/email/` | Envia PDF adjunto + link publico por email |
| Enviar por WhatsApp | `/presupuestos/<id>/whatsapp/` | Envia link publico por WhatsApp (Twilio) |
| Generar link publico | `/presupuestos/<id>/link/` | Genera token de 30 dias para el cliente |
| Revocar link | `/presupuestos/<id>/link/revocar/` | Invalida el token publico |
| Duplicar | `/presupuestos/<id>/duplicar/` | Crea copia en estado borrador |
| Guardar como plantilla | `/presupuestos/<id>/guardar-plantilla/` | Guarda como plantilla reutilizable |
| Ver historial | `/presupuestos/<id>/historial/` | Registro de todos los cambios (audit log) |
| Facturar (DTE) | `/presupuestos/<id>/facturar/` | Emitir factura SII (solo Pro) |

---

### 7.6 Firma digital del cliente

Flujo cuando el presupuesto esta en estado `enviado`:

1. El contratista genera un link publico desde la vista de detalle del presupuesto
2. Comparte el link con el cliente (por email, WhatsApp, o directamente)
3. El cliente abre el link sin necesidad de cuenta: `/presupuestos/ver/<token>/`
4. El cliente ve el detalle completo del presupuesto y firma en el canvas tactil
5. El sistema guarda: PNG de la firma, hash SHA-256, IP del cliente, User-Agent y timestamp
6. El presupuesto pasa automaticamente a estado `aceptado`

Rate limit de firma: 3 intentos por hora por IP (proteccion contra bots).

---

### 7.7 Versionado de presupuestos

Si editas un presupuesto en estado `enviado`, `aceptado` o `rechazado`:

- Se crea automaticamente una nueva version (v2, v3...) en estado `borrador`
- El presupuesto original se conserva intacto con todos sus datos
- Todas las versiones comparten el mismo numero de presupuesto
- Las versiones estan vinculadas por el campo `parent` (apunta a la version anterior)

Los presupuestos en `borrador` se editan directamente sin crear version nueva.

---

### 7.8 Plantillas reutilizables

URL: `/presupuestos/plantillas/`

Las plantillas son presupuestos sin cliente ni numero asignado, pensadas para trabajos frecuentes:

1. Crear un presupuesto con la estructura deseada (materiales, mano de obra, IVA, notas)
2. Ir a "Guardar como plantilla" desde la vista de detalle
3. La plantilla aparece en `/presupuestos/plantillas/`
4. Al crear un presupuesto nuevo, puedes cargar una plantilla como punto de partida

> Las plantillas **no cuentan** para el limite mensual del plan gratuito.

---

### 7.9 Dashboard y analytics

URL: `/dashboard/`

Metricas disponibles (actualizado cada 5 minutos con cache):

| Metrica | Descripcion |
|---------|-------------|
| Clientes activos | Total de clientes del contratista |
| Presupuestos del mes | Creados en el mes actual |
| Ingresos del mes | Suma de presupuestos aceptados este mes |
| Tasa de aceptacion | Porcentaje aceptados / totales |
| Top productos por margen | Productos propios mas rentables |
| CLV por cliente | Valor historico promedio por cliente |

---

## 8. Planes Free vs Pro

| Funcionalidad | Free | Pro ($9.990 CLP/mes) |
|---------------|:----:|:--------------------:|
| Presupuestos por mes | 5 | Ilimitados |
| Clientes | 10 | Ilimitados |
| Productos en catalogo | 20 | Ilimitados |
| Plantillas | Ilimitadas | Ilimitadas |
| PDF con marca propia | Si | Si |
| Firma digital del cliente | Si | Si |
| Link publico para cliente | Si | Si |
| Envio por email y WhatsApp | Si | Si |
| Historial de cambios | Si | Si |
| Precios de ferreterias | Si | Si |
| Facturacion DTE/SII | No | Si |

**Activar Pro:** `/usuarios/planes/checkout/`
**Gestionar suscripcion:** `/usuarios/mi-cuenta/facturacion/`
**Cancelar:** `/usuarios/mi-cuenta/facturacion/cancelar/`

**Estados de suscripcion:**

| Estado | Descripcion |
|--------|-------------|
| `active` | Suscripcion vigente (`is_pro() = True`) |
| `pending` | Checkout iniciado, pago sin confirmar |
| `cancelled` | Cancelada por el usuario |
| `past_due` | Pago fallido — se reintenta automaticamente |

---

## 9. API REST

La documentacion completa esta en [docs/api.md](api.md).

**Swagger UI interactivo:** `/api/v1/docs/`
**Schema OpenAPI:** `/api/v1/schema/`

### Autenticacion rapida

```bash
# Obtener token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@constructorexpress.cl", "password": "Demo1234!"}' # pragma: allowlist secret

# Token de acceso valido por 1 hora
# Token de renovacion valido por 7 dias
```

### Limites de tasa (throttling)

| Tipo | Limite |
|------|--------|
| Usuario autenticado | 1.000 requests/hora |
| Anonimo | 100 requests/hora |
| Obtencion de token (`/auth/token/`) | 5 requests/minuto |
| Sugerencias de productos | 60 requests/minuto por usuario |

---

## 10. Precios de ferreterias (scraping)

Constructor Express scrapea automaticamente precios de tres ferreterias chilenas y los muestra en el autocompletado al crear presupuestos.

### Ferreterias integradas

| Ferreteria | Tecnologia | Frecuencia |
|------------|-----------|-----------|
| Sodimac | JSON API interna | Semanal (dom. 3 AM) |
| Easy | VTEX API | Semanal (dom. 3 AM) |
| Imperial | HTML + BeautifulSoup | Semanal (dom. 3 AM) |

### Comportamiento del autocompletado

Al escribir en el campo de materiales de un presupuesto (minimo 3 caracteres):

1. Se muestran primero resultados de **Mi catalogo** (prioridad, hasta 5 resultados)
2. Luego resultados de **Ferreterias** con badge de color y link directo al producto en el sitio
3. Al seleccionar: rellena nombre y precio automaticamente
4. Tooltip: "Precio de referencia — ajusta tu margen"

**Scraping manual (para inicializar la BD en un servidor nuevo):**

```bash
# Scrapear todos (puede tardar varios minutos)
python manage.py scrape_retailers --retailer all

# Ver que se scrapearia sin guardar
python manage.py scrape_retailers --retailer all --dry-run
```

Los productos no vistos en mas de 60 dias se marcan como `is_active=False` automaticamente.

---

## 11. Arquitectura multi-tenant

Todos los datos estan aislados por contratista. No existe ninguna data compartida entre usuarios distintos:

- Cada modelo de dominio tiene `contractor = ForeignKey(User)`
- Los numeros de presupuesto son unicos **por contratista** (no globales)
- Todas las vistas filtran por `contractor=request.user`
- La helper `get_tenant_object_or_404(Model, pk, user)` previene acceso cruzado
- Intentar acceder a un recurso de otro usuario devuelve `404` (no `403`)

```python
# Patron correcto en todas las vistas y queries
budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
budgets = Budget.objects.filter(contractor=request.user)
```

El numero de presupuesto se auto-incrementa dentro de un bloque `select_for_update()` para evitar condiciones de carrera en entornos con multiples workers.

---

## 12. Seguridad

### Autenticacion y acceso

| Mecanismo | Configuracion |
|-----------|---------------|
| Hashing de contrasenas | PBKDF2 (Django default) |
| 2FA | TOTP (Google Authenticator, Authy, etc.) |
| Tokens JWT | Access: 1h · Refresh: 7d · Blacklist al revocar |
| Rate limit login | 5 req/min |
| Rate limit registro | 3 req/hora |
| Rate limit firma digital | 3 req/hora por IP |

### Validacion de archivos adjuntos

- Validacion por **magic bytes** (no solo por extension de archivo)
- Tipos aceptados: JPEG (`FF D8 FF`), PNG (`89 50 4E 47`), WEBP (`52 49 46 46`), PDF (`25 50 44 46`)
- Limite: 5 archivos por presupuesto, 5 MB por archivo

### Cabeceras HTTP y cookies

```
Cache-Control: no-store         (paginas autenticadas — previene back-button post-logout)
X-Frame-Options: DENY           (proteccion clickjacking)
X-Content-Type-Options: nosniff (proteccion MIME sniffing)
CSRF-Cookie-SameSite: Lax       (proteccion CSRF)
```

### Produccion (activado automaticamente si DEBUG=False)

```
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000   (HSTS por 1 año)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Audit log

`django-auditlog` registra todos los cambios en `Budget`, `BudgetItemMaterial`, `BudgetItemLabor`, `Client` y `Product` incluyendo usuario, timestamp y valores anteriores/nuevos.

Ver historial: `/presupuestos/<id>/historial/` (accesible solo por el contratista dueno del presupuesto).

### CI de seguridad (semanal, GitHub Actions)

- **Bandit:** analisis estatico de codigo (SAST), falla en severidad media o alta
- **pip-audit:** deteccion de vulnerabilidades en dependencias de produccion

---

## 13. Estructura del proyecto

```
constructor_express/
├── constructor_express/        # Configuracion central Django
│   ├── settings.py            # DB, apps, middleware, cache, Celery, JWT, Sentry
│   ├── urls.py                # Enrutamiento principal + montaje de API v1
│   ├── celery.py              # Configuracion de Celery
│   └── health.py              # Endpoint GET /healthz/ → 200 OK
│
├── users/                     # Autenticacion, perfiles, suscripciones, 2FA, billing
│   ├── models.py              # User (custom), ContractorProfile, Subscription, Payment
│   ├── views.py               # Login, registro, perfil, 2FA, dashboard, billing
│   ├── middleware.py          # NoCacheAuthMiddleware
│   ├── plan_guard.py          # Limites del plan gratuito (PLAN_FREE_MAX_*)
│   ├── webhooks.py            # Webhook MercadoPago con validacion HMAC
│   └── management/commands/
│       └── seed_demo.py       # Datos de demostracion
│
├── clients/                   # Gestion de clientes
│   ├── models.py              # Client
│   └── api_views.py           # ClientListAPIView, ClientDetailAPIView
│
├── catalog/                   # Catalogo de productos + scraping ferreterias
│   ├── models.py              # Product, RetailerProduct
│   ├── scrapers/              # BaseRetailerScraper, SodimacScraper, EasyScraper, ImperialScraper
│   ├── tasks.py               # scrape_all_retailers (Celery Beat, dom. 3 AM)
│   ├── api/
│   │   └── views.py           # ProductSuggestionsView (autocomplete)
│   └── management/commands/
│       ├── scrape_retailers.py
│       └── scrape_sodimac.py
│
├── budgets/                   # Dominio principal — presupuestos
│   ├── models.py              # Budget, BudgetItemMaterial, BudgetItemLabor,
│   │                          # BudgetSignature, BudgetAttachment, BudgetPublicToken
│   ├── managers.py            # BudgetQuerySet (analytics: CLV, top products, conversion rate)
│   ├── views.py               # CRUD, PDF, firma, versionado, plantillas, historial
│   ├── services/
│   │   ├── versioning.py      # create_new_version(), should_create_version()
│   │   ├── pdf.py             # Generacion de PDF (WeasyPrint)
│   │   └── whatsapp.py        # send_budget_whatsapp_task (Celery + Twilio)
│   ├── api/                   # BudgetViewSet + serializers con items anidados
│   ├── templatetags/
│   │   └── budget_filters.py  # Filtro |clp: $1.234.567
│   └── static/budgets/
│       ├── js/product_autocomplete.js   # Autocomplete vanilla JS (MutationObserver, debounce 300ms)
│       └── css/autocomplete.css
│
├── billing/                   # Facturacion DTE/SII (scaffolding) + MercadoPago checkout
│   ├── models.py              # Invoice, InvoiceLine
│   └── views.py               # Checkout, exito, fracaso
│
├── common/
│   └── tenant.py              # get_tenant_object_or_404()
│
├── templates/                 # Templates globales
│   ├── base.html              # Layout principal (navbar, alerts, footer)
│   ├── landing.html           # Landing page publica
│   ├── partials/              # Componentes reutilizables
│   └── emails/                # Plantillas de email transaccional
│
├── docs/
│   ├── api.md                 # Referencia completa de la API REST
│   └── guia-completa.md       # Este archivo
│
├── .github/workflows/
│   ├── ci.yml                 # Lint (ruff) + tests (pytest, cobertura 60%)
│   └── security.yml           # Bandit + pip-audit (semanal)
│
├── Dockerfile                 # Python 3.12-slim, usuario no-root, WeasyPrint libs
├── docker-compose.yml         # db + redis + web + worker
├── requirements.txt           # Dependencias de produccion (~69 paquetes)
├── requirements-dev.txt       # pytest, ruff, pre-commit, factory-boy
├── .pre-commit-config.yaml    # ruff, detect-secrets, django-upgrade
├── .env.example               # Plantilla de variables de entorno
└── conftest.py                # Configuracion pytest
```

---

## 14. Troubleshooting

### El servidor no inicia — "No module named 'X'"

```bash
# Verificar que el entorno virtual esta activado
which python  # Linux/macOS — debe mostrar la ruta del venv
# Windows: where python

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error de base de datos al migrar

```bash
# En desarrollo (SQLite): asegurarse de que no hay un db.sqlite3 corrupto
del db.sqlite3  # Windows
rm db.sqlite3   # Linux/macOS

python manage.py migrate
```

### Las sugerencias de ferreterias no aparecen

El autocompletado consulta la tabla `RetailerProduct`. Si esta vacia, hay que ejecutar el scraping:

```bash
python manage.py scrape_retailers --retailer all
# Puede tardar varios minutos
```

### Los emails no se envian en desarrollo

En desarrollo sin `SENDGRID_API_KEY`, Django usa el backend de consola. Los emails aparecen en la terminal del servidor de desarrollo, no en un buzón real.

### Celery no procesa tareas

```bash
# Verificar que Redis esta corriendo
redis-cli ping  # debe responder PONG

# Iniciar worker manualmente (desarrollo)
celery -A constructor_express worker --loglevel=info

# En Docker
docker-compose restart worker
```

### Errores de permisos en archivos estaticos

```bash
# Recolectar estaticos
python manage.py collectstatic --noinput

# En Docker — regenerar la imagen
docker-compose up --build web
```

---

*Constructor Express — Desarrollado en Chile para contratistas chilenos*
