# Constructor Express

> Plataforma SaaS de presupuestos profesionales para contratistas chilenos

**Demo en vivo:** [https://rodrigocl.alwaysdata.net](https://rodrigocl.alwaysdata.net)  
**Credenciales demo:** `demo@constructorexpress.cl` / `Demo1234!`

---

## Descripción

Constructor Express es una aplicación web para pequeños contratistas en Chile — gasfiteros, electricistas, carpinteros, pintores y más. Permite crear presupuestos profesionales en PDF, gestionar clientes, mantener un catálogo de productos y recibir la aceptación del cliente con firma digital, todo desde una interfaz simple y moderna.

---

## Funcionalidades

### Presupuestos
- Builder dinámico con materiales + mano de obra + IVA configurable
- PDF con logo y colores de marca del contratista
- Versionado automático: editar un presupuesto aceptado/enviado crea una versión nueva (v2, v3…) sin sobrescribir la original
- Firma digital del cliente en la vista pública (canvas HTML5 + SHA-256)
- Archivos adjuntos (fotos, planos, PDFs — máx. 5 × 5MB)
- Plantillas reutilizables para trabajos frecuentes
- Link público sin login para compartir con el cliente
- Envío por email y WhatsApp
- Historial de cambios (audit log) por campo

### Clientes y catálogo
- CRUD completo de clientes y productos
- Import/Export CSV del catálogo
- Autocompletado de materiales con precios de Sodimac, Easy e Imperial (scraper semanal)

### Analytics
- Dashboard con ingresos, tasa de conversión, alertas de vencimiento
- CLV por cliente, producto más rentable, tasa de aceptación mensual

### Pagos y facturación
- Checkout MercadoPago para suscripción Pro
- Scaffolding DTE/SII para factura electrónica

### Seguridad y calidad
- 2FA con TOTP (Google Authenticator)
- Rate limiting por IP y por usuario
- Audit log (django-auditlog) en Budget, Client y Product
- JWT para la API REST
- Tenant isolation estricto: cada query filtra por `contractor=request.user`

---

## Planes

| Feature | Básico (Gratis) | Pro |
|---|:-:|:-:|
| Presupuestos/mes | 5 | ∞ |
| Clientes | 10 | ∞ |
| Catálogo de productos | 20 | ∞ |
| PDF con marca propia | ✅ | ✅ |
| Link público + firma digital | ✅ | ✅ |
| Adjuntos (fotos/planos) | ✅ | ✅ |
| Plantillas reutilizables | ✅ | ✅ |
| Precios de ferreterías | ✅ | ✅ |
| Analytics avanzado | ✅ | ✅ |
| API REST + JWT | ✅ | ✅ |
| WhatsApp | ✅ | ✅ |
| Facturación DTE (SII) | ❌ | ✅ |

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| **Backend** | Python 3.12 + Django 5.2 |
| **API** | Django REST Framework + SimpleJWT + drf-spectacular |
| **Base de datos** | PostgreSQL (producción) / SQLite (desarrollo) |
| **Frontend** | HTML + Tailwind CSS + JS vanilla |
| **Task queue** | Celery + Redis + django-celery-beat |
| **Scraping** | httpx async + BeautifulSoup4 + lxml |
| **Audit log** | django-auditlog |
| **PDF** | WeasyPrint (dev/Docker) / xhtml2pdf (alwaysdata) |
| **Email** | Anymail/SendGrid (prod) + Twilio WhatsApp |
| **Pagos** | MercadoPago |
| **Observabilidad** | Sentry + python-json-logger |
| **Servidor** | Gunicorn + WhiteNoise |

---

## Instalación local

### Requisitos
- Python 3.12+
- Git

### Pasos

```bash
# 1. Clonar
git clone <repo-url>
cd constructor_express

# 2. Entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Migraciones (SQLite automático si no hay DB_NAME)
python manage.py migrate

# 5. Datos de demo
python manage.py seed_demo

# 6. Servidor
python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000**

---

## Docker (con PostgreSQL)

```bash
# Requiere .env_producion con SECRET_KEY y POSTGRES_PASSWORD
docker-compose up --build
```

Incluye: Postgres + Gunicorn + Celery worker + Celery Beat (scrapers).

---

## Variables de entorno

Copia `.env.example` a `.env_producion` y completa:

```env
SECRET_KEY=clave-secreta-larga
DEBUG=False
ALLOWED_HOSTS=tudominio.cl

# PostgreSQL (solo producción)
DB_NAME=constructor_express
DB_USER=usuario
DB_PASS=contraseña
DB_HOST=localhost

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxx

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0

# MercadoPago
MP_ACCESS_TOKEN=APP_USR-xxx
MP_PUBLIC_KEY=APP_USR-xxx
MP_WEBHOOK_SECRET=xxx

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx
```

> En desarrollo local no necesitas el archivo — usa SQLite y email por consola automáticamente.

---

## Comandos de gestión

```bash
# Datos de demo
python manage.py seed_demo

# Scraping manual de ferreterías
python manage.py scrape_retailers --retailer all
python manage.py scrape_retailers --retailer sodimac --dry-run
python manage.py scrape_sodimac --dry-run

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Tests
python manage.py test budgets clients catalog

# Colectar estáticos
python manage.py collectstatic --noinput
```

---

## API REST

Documentación completa en [docs/api.md](docs/api.md) y Swagger en `/api/v1/docs/`.

**Autenticación:** JWT Bearer token.

### Endpoints resumen

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/token/` | Obtener access + refresh token |
| `POST` | `/api/v1/auth/refresh/` | Renovar access token |
| `POST` | `/api/v1/auth/blacklist/` | Revocar refresh token |
| `GET` | `/api/v1/stats/` | Stats del dashboard |
| `GET` | `/api/v1/presupuestos/` | Listar presupuestos (`?status=`) |
| `GET` | `/api/v1/presupuestos/{id}/` | Detalle con ítems |
| `GET/POST` | `/api/v1/presupuestos/write/` | CRUD completo con ítems |
| `GET/PUT/PATCH/DELETE` | `/api/v1/presupuestos/write/{id}/` | Detalle CRUD |
| `GET/POST` | `/api/v1/clientes/` | Listar / crear clientes |
| `GET/PUT/PATCH/DELETE` | `/api/v1/clientes/{id}/` | CRUD cliente |
| `GET/POST` | `/api/v1/productos/` | Listar / crear productos (`?q=`) |
| `GET/PUT/PATCH/DELETE` | `/api/v1/productos/{id}/` | CRUD producto |
| `GET` | `/api/v1/productos/sugerencias/` | Sugerencias ferreterías + catálogo (`?q=`) |
| `GET` | `/api/v1/schema/` | OpenAPI schema |
| `GET` | `/api/v1/docs/` | Swagger UI |

---

## Estructura del proyecto

```
constructor_express/
├── constructor_express/      # Config principal
│   ├── settings.py           # Variables, DB, Celery, JWT, Sentry…
│   ├── urls.py               # URLs raíz + API
│   └── celery.py             # App Celery
│
├── users/                    # Auth, perfil, dashboard, pagos, 2FA
├── clients/                  # CRUD clientes
├── catalog/                  # Catálogo de productos + scrapers ferreterías
│   ├── models.py             # Product, RetailerProduct
│   ├── scrapers/             # BaseRetailerScraper, SodimacScraper, EasyScraper, ImperialScraper
│   ├── tasks.py              # Celery task: scrape_all_retailers (semanal)
│   ├── api/                  # ProductSuggestionsView
│   └── management/commands/  # scrape_retailers, scrape_sodimac
│
├── budgets/                  # Core: presupuestos
│   ├── models.py             # Budget (version/parent/is_template), BudgetItem*, BudgetSignature, BudgetAttachment, BudgetPublicToken
│   ├── managers.py           # BudgetQuerySet con analytics
│   ├── services/
│   │   ├── versioning.py     # create_new_version()
│   │   └── whatsapp.py       # send_budget_whatsapp_task
│   ├── api/                  # BudgetViewSet (escritura completa)
│   └── templates/budgets/    # list, detail, form, pdf, public_view, history, signature…
│
├── billing/                  # MercadoPago checkout + DTE scaffolding
├── templates/                # base.html, landing.html, partials/
├── docs/
│   └── api.md                # Documentación completa de la API
├── sprint/                   # Plan de sprints de desarrollo
└── docker-compose.yml
```

---

## Modelos de datos

```
User
 ├── ContractorProfile          (empresa, logo, colores de marca)
 ├── Client[]
 │    └── Budget[]
 │         ├── version, parent  (versionado)
 │         ├── is_template      (plantillas)
 │         ├── BudgetItemMaterial[]
 │         ├── BudgetItemLabor[]
 │         ├── BudgetPublicToken (link público con expiración)
 │         ├── BudgetSignature   (firma digital del cliente)
 │         └── BudgetAttachment[] (fotos, planos, PDFs)
 └── Product[]                  (catálogo propio)

RetailerProduct                 (caché precios Sodimac/Easy/Imperial)
```

---

## Tests

```bash
python manage.py test budgets clients catalog
```

---

## Localización Chile

- Precios en CLP sin decimales — filtro `|clp` → `$1.234.567`
- Zona horaria `America/Santiago`
- IVA configurable por presupuesto (habitualmente 0% o 19%)
- Idioma `es-cl`
- RUT en clientes

---

## Licencia

Proyecto privado — todos los derechos reservados.

---

*Desarrollado en Chile 🇨🇱*
