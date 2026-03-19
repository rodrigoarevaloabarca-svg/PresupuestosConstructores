# 🏗️ Constructor Express

> Plataforma SaaS de presupuestos profesionales para contratistas chilenos

**Demo en vivo:** [https://rodrigocl.alwaysdata.net](https://rodrigocl.alwaysdata.net)

---

## 📋 Descripción

Constructor Express es una aplicación web diseñada para pequeños contratistas y reparadores de oficio en Chile — gasfiteros, electricistas, carpinteros, pintores y más. Permite crear presupuestos profesionales en PDF, gestionar clientes y mantener un catálogo de productos y materiales, todo desde una interfaz simple y moderna.

### ¿Para quién es?

- Gasfiteros, electricistas, carpinteros, pintores
- Constructores independientes
- Cualquier contratista que necesite presupuestar trabajos de forma profesional

---

## ✅ Funcionalidades

### MVP (disponible ahora)

| Módulo | Descripción |
|---|---|
| 🔐 **Autenticación** | Registro, login seguro, cambio de contraseña |
| 🏢 **Perfil de empresa** | Logo, RUT, colores de marca, datos de contacto |
| 👥 **Clientes** | CRUD completo con historial de presupuestos |
| 📦 **Catálogo** | Productos con precio costo/venta, margen, import/export CSV |
| 📄 **Presupuestos** | Builder dinámico con materiales + mano de obra + IVA |
| 🔗 **Link público** | Compartir presupuesto con cliente sin que tenga cuenta |
| 📧 **Email** | Envío de presupuesto por correo al cliente |
| 📋 **Duplicar** | Copiar un presupuesto con 1 clic |
| 🖨️ **PDF** | Generación con logo y colores de marca |
| 📊 **Dashboard** | Stats, alertas de vencimiento, ingresos |
| 📈 **Reportes** | Gráficos de actividad, conversión, ingresos por mes |
| 🔍 **Búsqueda global** | Busca en clientes, presupuestos y productos |
| 🌐 **API REST** | Endpoints JSON para futura app móvil |

### Planes

| Feature | Básico (Gratis) | Pro |
|---|:-:|:-:|
| Presupuestos/mes | 5 | ∞ |
| Clientes | 10 | ∞ |
| Catálogo de productos | 20 | ∞ |
| PDF con marca propia | ✅ | ✅ |
| Link público para cliente | ✅ | ✅ |
| Reportes y analíticas | ✅ | ✅ |
| Import/Export CSV | ✅ | ✅ |
| API REST | ✅ | ✅ |
| Facturación DTE (próximo) | ❌ | ✅ |
| Firma digital (próximo) | ❌ | ✅ |

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12 + Django 4.2 |
| **API** | Django REST Framework |
| **Base de datos** | PostgreSQL (producción) / SQLite (desarrollo) |
| **Frontend** | HTML + Tailwind CSS + JavaScript |
| **Archivos estáticos** | WhiteNoise |
| **PDF** | xhtml2pdf |
| **Servidor** | uWSGI (alwaysdata) |
| **Hosting** | alwaysdata.com |

---

## 📁 Estructura del Proyecto

```
PresupuestosConstructores/
│
├── constructor_express/        # Configuración principal Django
│   ├── settings.py             # Config (local + producción)
│   ├── urls.py                 # URLs principales + API
│   └── wsgi.py                 # Punto entrada WSGI (local)
│
├── users/                      # App: usuarios y autenticación
│   ├── models.py               # User, ContractorProfile
│   ├── views.py                # Login, registro, perfil
│   ├── dashboard_views.py      # Dashboard con stats y alertas
│   ├── reports_view.py         # Reportes con Chart.js
│   ├── search_view.py          # Búsqueda global
│   ├── landing_view.py         # Landing page pública
│   ├── middleware.py           # NoCacheAuth (seguridad logout)
│   ├── context_processors.py  # Perfil disponible en todos los templates
│   ├── templates/users/        # Templates de la app
│   └── management/commands/
│       ├── seed_demo.py        # Datos de demostración
│       └── clean_data.py       # Limpiar BD conservando catálogo
│
├── clients/                    # App: gestión de clientes
│   ├── models.py               # Client
│   ├── views.py                # CRUD clientes
│   ├── serializers.py          # DRF serializer
│   ├── api_views.py            # API REST endpoints
│   └── templates/clients/
│
├── catalog/                    # App: catálogo de productos
│   ├── models.py               # Product
│   ├── views.py                # CRUD + import/export CSV
│   ├── serializers.py
│   ├── api_views.py
│   └── templates/catalog/
│
├── budgets/                    # App: presupuestos (core del negocio)
│   ├── models.py               # Budget, BudgetItemMaterial, BudgetItemLabor, BudgetPublicToken
│   ├── views.py                # CRUD + PDF + duplicate + public link + email
│   ├── email_utils.py          # Envío de presupuesto por correo
│   ├── serializers.py
│   ├── api_views.py
│   ├── templatetags/
│   │   └── budget_filters.py   # Filtro |clp (pesos chilenos)
│   └── templates/
│       ├── budgets/            # Templates de presupuestos
│       └── emails/             # Templates de email
│
├── templates/                  # Templates globales
│   ├── base.html               # Layout principal con sidebar
│   ├── landing.html            # Landing page
│   └── partials/
│       └── pagination.html
│
├── static/                     # Archivos estáticos
│   ├── css/main.css
│   └── js/main.js
│
├── wsgi_production.py          # Punto entrada WSGI (producción alwaysdata)
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🚀 Instalación Local

### Requisitos
- Python 3.10+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/rodrigoarevaloabarca-svg/PresupuestosConstructores.git
cd PresupuestosConstructores

# 2. Crear entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Migraciones (usa SQLite automáticamente en local)
python manage.py migrate

# 5. Cargar datos de demo
python manage.py seed_demo

# 6. Iniciar servidor
python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000**

**Credenciales demo:**
- Email: `demo@constructorexpress.cl`
- Contraseña: `Demo1234!`

---

## ⚙️ Variables de Entorno

Copia `.env.example` a `.env` y completa los valores:

```env
SECRET_KEY=clave-secreta-larga-y-unica
DEBUG=False
ALLOWED_HOSTS=tudominio.cl

# Base de datos PostgreSQL (solo producción)
DB_NAME=nombre_base_datos
DB_USER=usuario
DB_PASS=contraseña
DB_HOST=host-postgresql
```

> En desarrollo local **no necesitas** el `.env` — usa SQLite automáticamente.

---

## 🌐 API REST

Todos los endpoints requieren autenticación.

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/v1/stats/` | Estadísticas del dashboard |
| `GET` | `/api/v1/presupuestos/` | Listar presupuestos |
| `GET` | `/api/v1/presupuestos/{id}/` | Detalle con ítems |
| `GET/POST` | `/api/v1/clientes/` | Listar / crear clientes |
| `GET/PUT/DELETE` | `/api/v1/clientes/{id}/` | CRUD cliente |
| `GET/POST` | `/api/v1/productos/` | Listar / crear productos |
| `GET/PUT/DELETE` | `/api/v1/productos/{id}/` | CRUD producto |

### Ejemplo de respuesta

```json
GET /api/v1/presupuestos/1/

{
  "id": 1,
  "number": 1,
  "title": "Reparación baño principal",
  "client_name": "María González",
  "status": "enviado",
  "status_display": "Enviado al Cliente",
  "subtotal_materials": 122700,
  "subtotal_labor": 130000,
  "total": 252700,
  "valid_until": "2024-04-03",
  "material_items": [...],
  "labor_items": [...]
}
```

---

## 🗄️ Modelos de Datos

```
User ──────────────────────────┐
  │                            │
  ├── ContractorProfile        │ (perfil de empresa)
  │                            │
  ├── Client[] ────────────────┤
  │     └── Budget[] ──────────┤
  │           ├── BudgetItemMaterial[]
  │           ├── BudgetItemLabor[]
  │           └── BudgetPublicToken
  │
  └── Product[] (catálogo)
```

---

## 🧪 Tests

```bash
python manage.py test budgets clients catalog
```

18 tests unitarios cubriendo:
- Modelos (cálculo de totales, márgenes, numeración)
- Vistas (autenticación, CRUD, aislamiento de datos)
- API REST (endpoints, permisos)

---

## 📦 Comandos de Gestión

```bash
# Crear datos de demostración
python manage.py seed_demo

# Limpiar BD conservando el catálogo de productos
python manage.py clean_data

# Limpiar BD de un usuario específico
python manage.py clean_data --email=tu@email.cl

# Limpiar todo incluyendo productos
python manage.py clean_data --all
```

---

## 🔄 Flujo de Actualización en Producción

```bash
# 1. En tu PC — subir cambios
git add .
git commit -m "descripción del cambio"
git push

# 2. En alwaysdata por SSH
cd /home/rodrigocl/PresupuestosConstructores/
git pull
source .venv/bin/activate

# Solo si cambiaste modelos
python manage.py migrate

# Solo si cambiaste CSS/JS/imágenes
python manage.py collectstatic --noinput

# 3. Reiniciar desde el panel
# admin.alwaysdata.com → Web → Sitios → Reiniciar
```

---

## 🇨🇱 Localización Chile

- Validación de RUT chileno
- Precios en Pesos Chilenos (CLP) sin decimales — filtro `|clp` → `$1.234.567`
- Zona horaria: `America/Santiago`
- IVA configurable por presupuesto (0% o 19%)
- Idioma: Español chileno (`es-cl`)

---

## 🛣️ Roadmap

- [ ] Generación de PDF con WeasyPrint (requiere Linux)
- [ ] Integración Webpay Plus / Khipu (pagos en línea)
- [ ] Facturación electrónica DTE (SII Chile)
- [ ] Firma digital del presupuesto por el cliente
- [ ] Módulo de gastos por obra
- [ ] Múltiples usuarios por empresa
- [ ] App móvil (API REST ya implementada)

---

## 📄 Licencia

Proyecto privado — todos los derechos reservados.

---

*Desarrollado con ❤️ en Chile 🇨🇱*
