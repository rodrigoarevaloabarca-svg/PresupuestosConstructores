# Constructor Express

> Plataforma SaaS de presupuestos profesionales para contratistas chilenos

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14-red)](https://django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery)](https://docs.celeryq.dev)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](/.github/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-60%25_min-brightgreen)](conftest.py)
[![License](https://img.shields.io/badge/Licencia-Privada-lightgrey)](LICENSE)

**Demo en vivo:** [https://rodrigocl.alwaysdata.net](https://rodrigocl.alwaysdata.net)
**Credenciales demo:** `demo@constructorexpress.cl` / `Demo1234!`

---

## Descripcion

Constructor Express permite a pequeños contratistas en Chile — gasfiteros, electricistas, carpinteros, pintores — crear presupuestos PDF profesionales, gestionar clientes, mantener un catálogo de materiales con precios de ferreterías en tiempo real, y recibir la aceptación del cliente con firma digital, todo desde una interfaz web simple y moderna.

---

## Funcionalidades

### Presupuestos
- Builder dinámico con materiales + mano de obra + IVA configurable (0% o 19%)
- PDF con logo, colores de marca y datos de empresa del contratista
- Versionado automático: editar un presupuesto enviado o aceptado crea una revisión nueva (v2, v3...) sin sobrescribir el original
- Firma digital del cliente en vista pública (canvas HTML5, hash SHA-256, IP, user-agent)
- Archivos adjuntos: fotos, planos y PDFs hasta 5 archivos × 5 MB, validados por magic bytes
- Plantillas reutilizables para trabajos frecuentes (no cuentan para el límite mensual)
- Link público con expiración de 30 días para compartir sin que el cliente tenga cuenta
- Envío por email (PDF adjunto) y WhatsApp (link público vía Twilio)
- Historial de cambios por campo con django-auditlog

### Clientes y catalogo
- CRUD completo de clientes y productos
- Import/export del catálogo en CSV (hasta 5.000 filas)
- Autocompletado de materiales con precios de Sodimac, Easy e Imperial en tiempo real
- Scraping semanal automático (Celery Beat, domingos 3 AM)

### Analytics
- Dashboard con ingresos del mes, tasa de conversión y alertas de vencimiento
- CLV por cliente, productos por margen, tasa de aceptación mensual

### Pagos y facturacion
- Suscripción Pro vía MercadoPago ($9.990 CLP/mes)
- Scaffolding DTE/SII para factura electrónica (solo plan Pro)

### Seguridad
- Autenticación con 2FA TOTP (Google Authenticator, Authy)
- Rate limiting por IP y por usuario en endpoints críticos
- Tenant isolation estricto: cada query filtra por `contractor=request.user`
- JWT para la API REST (access 1 h, refresh 7 días, blacklist al revocar)
- Cabeceras HTTP de seguridad (CSP, HSTS, X-Frame-Options)
- CI con análisis estático (Bandit) y auditoría de dependencias (pip-audit)

---

## Stack tecnologico

| Capa | Tecnologia |
|------|------------|
| Backend | Python 3.12 + Django 5.2 |
| API REST | Django REST Framework 3.14 + SimpleJWT + drf-spectacular |
| Base de datos | PostgreSQL 15 (produccion) / SQLite (desarrollo) |
| Frontend | HTML + Tailwind CSS + JavaScript vanilla |
| Task queue | Celery 5.3 + Redis 7 + django-celery-beat |
| Scraping | httpx async + BeautifulSoup4 + lxml + rapidfuzz |
| PDF | WeasyPrint (dev/Docker) / xhtml2pdf (alwaysdata) |
| Email | django-anymail / SendGrid |
| WhatsApp | Twilio |
| Pagos | MercadoPago |
| 2FA | django-otp + TOTP |
| Audit log | django-auditlog |
| Observabilidad | Sentry + python-json-logger |
| Servidor | Gunicorn + WhiteNoise |

---

## Instalacion local (desarrollo)

### Requisitos

- Python 3.12+
- Git

SQLite esta incluido en Python — no se necesita ninguna base de datos adicional para desarrollo.

### Pasos

```bash
# 1. Clonar
git clone <repo-url>
cd constructor_express

# 2. Entorno virtual
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Migraciones (SQLite automatico — no se requiere configuracion)
python manage.py migrate

# 5. Datos de demostracion
python manage.py seed_demo

# 6. Servidor
python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000**

> Si `DB_NAME` no esta definida como variable de entorno, Django usa SQLite automaticamente. No es necesario crear ningun archivo `.env` para desarrollo local.

---

## Docker (PostgreSQL + Celery)

```bash
# Requiere .env_producion con SECRET_KEY y POSTGRES_PASSWORD
cp .env.example .env_producion
# Editar .env_producion con los valores correspondientes

docker-compose up --build
```

Levanta cuatro servicios: PostgreSQL 15, Redis 7, Gunicorn (3 workers) y Celery worker. Al iniciar aplica migraciones y carga datos demo automaticamente si `DEBUG=True`.

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| `db` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Redis 7 (broker Celery) |
| `web` | 8000 | Gunicorn — healthcheck en `/healthz/` |
| `worker` | — | Celery worker + Beat |

```bash
# Comandos utiles con Docker
docker-compose logs -f web              # Ver logs en tiempo real
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose restart worker
docker-compose down -v                  # Detener y borrar volúmenes (incluye BD)
```

---

## Variables de entorno

Copia `.env.example` a `.env_producion` y configura los valores. En desarrollo no se necesita este archivo.

### Obligatorias en produccion

| Variable | Descripcion |
|----------|-------------|
| `SECRET_KEY` | Clave secreta Django (minimo 50 caracteres, aleatoria) |
| `DEBUG` | `False` en produccion |
| `ALLOWED_HOSTS` | Dominios separados por coma (`tudominio.cl,www.tudominio.cl`) |
| `POSTGRES_DB` | Nombre de la base de datos |
| `POSTGRES_USER` | Usuario PostgreSQL |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL |

### Servicios externos (opcionales)

| Variable | Servicio | Para que sirve |
|----------|----------|---------------|
| `SENDGRID_API_KEY` | SendGrid | Envio de presupuestos por email |
| `CELERY_BROKER_URL` | Redis | Cola de tareas async |
| `MP_ACCESS_TOKEN` | MercadoPago | Cobro de suscripciones Pro |
| `MP_WEBHOOK_SECRET` | MercadoPago | Validacion HMAC de webhooks |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | Twilio | Envio por WhatsApp |
| `TWILIO_WHATSAPP_FROM` | Twilio | Numero WhatsApp remitente |
| `SII_PROVIDER_API_KEY` | OpenFactura | Emision DTE/SII (solo Pro) |
| `SENTRY_DSN` | Sentry | Monitoreo de errores |

---

## Comandos de gestion

```bash
# Datos de demostracion
python manage.py seed_demo              # Crea usuario, clientes, productos y presupuestos
python manage.py seed_demo --reset      # Elimina y recrea desde cero

# Scraping manual de ferreterias
python manage.py scrape_retailers --retailer all
python manage.py scrape_retailers --retailer sodimac|easy|imperial
python manage.py scrape_retailers --retailer all --dry-run

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Tests
python manage.py test budgets clients catalog
python manage.py test budgets.tests.BudgetModelTests.test_total_calculation

# Estaticos (necesario antes de DEBUG=False)
python manage.py collectstatic --noinput
```

---

## API REST

Documentacion completa en [docs/api.md](docs/api.md). Swagger UI interactivo en `/api/v1/docs/`.

**Autenticacion:** JWT Bearer token. Access token: 1 hora. Refresh token: 7 dias.

```bash
# Obtener token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@constructorexpress.cl", "password": "Demo1234!"}' # pragma: allowlist secret

# Usar token en requests
curl http://localhost:8000/api/v1/presupuestos/ \
  -H "Authorization: Bearer <access_token>"
```

### Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/token/` | Obtener access + refresh token |
| `POST` | `/api/v1/auth/refresh/` | Renovar access token |
| `POST` | `/api/v1/auth/blacklist/` | Revocar refresh token |
| `GET` | `/api/v1/stats/` | Estadisticas del dashboard |
| `GET` | `/api/v1/presupuestos/` | Listar presupuestos (`?status=`) |
| `GET` | `/api/v1/presupuestos/{id}/` | Detalle con items |
| `GET/POST` | `/api/v1/presupuestos/write/` | CRUD completo con items anidados |
| `GET/PUT/PATCH/DELETE` | `/api/v1/presupuestos/write/{id}/` | CRUD detalle |
| `GET/POST` | `/api/v1/clientes/` | Listar / crear clientes |
| `GET/PUT/PATCH/DELETE` | `/api/v1/clientes/{id}/` | CRUD cliente |
| `GET/POST` | `/api/v1/productos/` | Listar / crear productos (`?q=`) |
| `GET/PUT/PATCH/DELETE` | `/api/v1/productos/{id}/` | CRUD producto |
| `GET` | `/api/v1/productos/sugerencias/` | Autocomplete catalogo + ferreterias (`?q=`) |
| `GET` | `/api/v1/schema/` | OpenAPI schema (JSON) |
| `GET` | `/api/v1/docs/` | Swagger UI |

**Throttling:** 1.000 req/hora (autenticado) · 100 req/hora (anonimo) · 60 req/min (sugerencias)
**Paginacion:** `?page=N` — 20 resultados por pagina

---

## Planes

| Funcionalidad | Basico (Gratis) | Pro ($9.990 CLP/mes) |
|---------------|:-:|:-:|
| Presupuestos por mes | 5 | Ilimitados |
| Clientes | 10 | Ilimitados |
| Catalogo de productos | 20 | Ilimitados |
| PDF con marca propia | ✓ | ✓ |
| Link publico + firma digital | ✓ | ✓ |
| Adjuntos (fotos/planos/PDFs) | ✓ | ✓ |
| Plantillas reutilizables | ✓ | ✓ |
| Precios de ferreterias | ✓ | ✓ |
| Analytics avanzado | ✓ | ✓ |
| API REST + JWT | ✓ | ✓ |
| Envio WhatsApp y email | ✓ | ✓ |
| Facturacion DTE/SII | — | ✓ |

---

## Arquitectura

### Aplicaciones Django (5 dominios)

| App | Dominio | Modelos principales |
|-----|---------|---------------------|
| `users` | Autenticacion, perfiles, suscripciones, 2FA | `User`, `ContractorProfile`, `Subscription`, `Payment` |
| `clients` | CRUD de clientes | `Client` |
| `catalog` | Catalogo propio + scraping ferreterias | `Product`, `RetailerProduct` |
| `budgets` | Presupuestos (dominio principal) | `Budget`, `BudgetItemMaterial`, `BudgetItemLabor`, `BudgetSignature`, `BudgetAttachment`, `BudgetPublicToken` |
| `billing` | Facturacion DTE/SII y pagos | `Invoice`, `InvoiceLine` |

### Multi-tenancy

Todos los objetos de dominio tienen `contractor = ForeignKey(User)`. Las vistas siempre filtran por `contractor=request.user`. Los numeros de presupuesto son unicos **por contratista**, no globales.

### Modelo de datos

```
User
 ├── ContractorProfile      (empresa, logo, colores de marca)
 ├── Subscription           (plan Pro, estado, proxima cobranza)
 ├── Client[]
 │    └── Budget[]
 │         ├── version / parent      (versionado)
 │         ├── is_template           (plantillas reutilizables)
 │         ├── BudgetItemMaterial[]  (materiales, vinculados opcionalmente a Product)
 │         ├── BudgetItemLabor[]     (mano de obra)
 │         ├── BudgetPublicToken     (link publico, expira en 30 dias)
 │         ├── BudgetSignature       (firma digital del cliente: PNG + SHA-256)
 │         ├── BudgetAttachment[]    (fotos, planos, PDFs — max 5 × 5 MB)
 │         └── Invoice               (factura DTE, solo Pro)
 └── Product[]              (catalogo propio: costo, venta, margen %)

RetailerProduct[]           (cache de precios Sodimac / Easy / Imperial)
```

### Estructura del repositorio

```
constructor_express/
├── constructor_express/      # Config central (settings, urls, celery, health)
├── users/                    # Auth, perfil, dashboard, pagos, 2FA, signals
├── clients/                  # CRUD clientes
├── catalog/                  # Catalogo + scrapers (sodimac, easy, imperial)
│   └── scrapers/             # BaseRetailerScraper + 3 implementaciones async
├── budgets/                  # Presupuestos (core del negocio)
│   ├── services/             # versioning.py, whatsapp.py, pdf.py
│   ├── api/                  # BudgetViewSet + serializers anidados
│   └── static/budgets/js/    # product_autocomplete.js (vanilla, MutationObserver)
├── billing/                  # MercadoPago checkout + DTE scaffolding
├── common/                   # tenant.py (get_tenant_object_or_404)
├── templates/                # base.html, landing.html, partials/
├── docs/                     # api.md, guia-completa.md
├── .github/workflows/        # ci.yml (lint + tests), security.yml (bandit + pip-audit)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Localizacion Chile

- Moneda CLP sin decimales — filtro `|clp` → `$1.234.567`
- Zona horaria `America/Santiago`
- IVA configurable por presupuesto (0% o 19%)
- Idioma `es-cl`
- RUT en formato `12.345.678-9`

---

## Tests y calidad

```bash
# Suite completa (SQLite en memoria, Celery sincrono)
python manage.py test budgets clients catalog

# Con cobertura (pytest)
pytest --cov --cov-fail-under=60
```

CI en GitHub Actions ejecuta en cada push/PR:
1. **Lint:** ruff check + ruff format
2. **Tests:** pytest con cobertura minima del 60%
3. **Seguridad (semanal):** bandit (SAST) + pip-audit (vulnerabilidades en dependencias)

---

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| [docs/api.md](docs/api.md) | Referencia completa de la API REST |
| [docs/guia-completa.md](docs/guia-completa.md) | Guia de instalacion, uso y operacion |
| `/api/v1/docs/` | Swagger UI interactivo (requiere servidor activo) |
| `/api/v1/schema/` | Schema OpenAPI en JSON |

---

## Licencia

Proyecto privado — todos los derechos reservados.

Desarrollado en Chile para contratistas chilenos.
