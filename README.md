# 🏗️ Constructor Express
> Plataforma SaaS de presupuestos para contratistas chilenos

---

## 🚀 Inicio Rápido (Desarrollo)

```bash
# 1. Clonar / descomprimir
cd constructor_express/

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Variables de entorno (opcional en dev)
cp .env.example .env            # editar si se desea

# 5. Migraciones
python manage.py migrate

# 6. Datos de demo
python manage.py seed_demo

# 7. Iniciar
python manage.py runserver
```

**Acceso demo:** http://localhost:8000  
**Email:** `demo@constructorexpress.cl` | **Contraseña:** `Demo1234!`  
**Admin:** http://localhost:8000/admin/

---

## 🐳 Docker (Recomendado)

```bash
docker-compose up --build
```
La aplicación estará en http://localhost:8000 con demo incluido.

---

## 📁 Estructura del Proyecto

```
constructor_express/
├── users/                  # Auth, perfiles de empresa, dashboard, reportes
│   ├── models.py           # User (custom), ContractorProfile
│   ├── views.py            # Login, register, profile, change_password
│   ├── dashboard_views.py  # Dashboard con stats
│   ├── reports_view.py     # Analíticas con Chart.js
│   ├── landing_view.py     # Landing page pública
│   └── context_processors.py
├── clients/                # Gestión de clientes
│   ├── models.py           # Client
│   ├── views.py            # CRUD + API REST
│   ├── serializers.py      # DRF serializers
│   └── api_views.py
├── catalog/                # Catálogo de productos
│   ├── models.py           # Product
│   ├── views.py            # CRUD + CSV import/export
│   ├── serializers.py
│   └── api_views.py
├── budgets/                # Motor de presupuestos (core)
│   ├── models.py           # Budget, BudgetItemMaterial, BudgetItemLabor, BudgetPublicToken
│   ├── views.py            # CRUD + PDF + duplicate + public link
│   ├── serializers.py
│   ├── api_views.py
│   └── templatetags/
│       └── budget_filters.py  # Filtro |clp para pesos chilenos
├── templates/
│   ├── base.html              # Layout principal con sidebar
│   ├── landing.html           # Landing page
│   ├── users/                 # Login, register, dashboard, reports, profile
│   ├── clients/               # CRUD clientes
│   ├── catalog/               # CRUD + import CSV
│   └── budgets/               # CRUD + PDF + vista pública
├── constructor_express/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── deploy.sh               # Script Ubuntu + Nginx + Gunicorn
└── .env.example
```

---

## ✅ Funcionalidades Implementadas

| Módulo | Funcionalidad |
|--------|--------------|
| 🔐 **Auth** | Registro, login, perfil empresa, cambio de contraseña |
| 👥 **Clientes** | CRUD completo, historial presupuestos, búsqueda |
| 📦 **Catálogo** | CRUD, precios costo/venta, margen, import/export CSV |
| 📄 **Presupuestos** | Builder dinámico, materiales + mano de obra, IVA |
| 🔗 **Link público** | Compartir presupuesto con cliente sin login |
| 📊 **Dashboard** | Stats en tiempo real, presupuestos recientes |
| 📈 **Reportes** | Gráficos Chart.js, ingresos por mes, tasa de conversión |
| 🖨️ **PDF** | WeasyPrint con logo, colores de marca, totales |
| 📋 **Duplicar** | Copia de presupuesto con 1 clic |
| 🌐 **API REST** | Endpoints JSON para futura app móvil |
| 🧪 **Tests** | 18 tests unitarios e integración |

---

## 🌐 API REST

Todos los endpoints requieren autenticación (sesión o Basic Auth).

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/stats/` | Estadísticas del dashboard |
| GET/POST | `/api/v1/presupuestos/` | Listar presupuestos |
| GET | `/api/v1/presupuestos/{id}/` | Detalle con ítems |
| GET/POST | `/api/v1/clientes/` | Listar / crear clientes |
| GET/PUT/DELETE | `/api/v1/clientes/{id}/` | CRUD cliente |
| GET/POST | `/api/v1/productos/` | Listar / crear productos |
| GET/PUT/DELETE | `/api/v1/productos/{id}/` | CRUD producto |

---

## 🗃️ Base de Datos en Producción (PostgreSQL)

```bash
# Variables de entorno
DATABASE_URL=postgres://usuario:pass@host:5432/db_name
```

---

## 📦 Planes

| Feature | Básico (Gratis) | Pro |
|---------|:-:|:-:|
| Presupuestos/mes | 5 | ∞ |
| Clientes | 10 | ∞ |
| Productos catálogo | 20 | ∞ |
| PDF con marca propia | ✅ | ✅ |
| Link público para cliente | ✅ | ✅ |
| Reportes y analíticas | ✅ | ✅ |
| Import/Export CSV | ✅ | ✅ |
| API REST | ✅ | ✅ |
| Facturación DTE (próximo) | ❌ | ✅ |
| Firma digital (próximo) | ❌ | ✅ |

---

## 🛣️ Roadmap

- [ ] Integración Webpay Plus / Khipu (cobros en línea)
- [ ] Facturación electrónica DTE (SII Chile)
- [ ] Firma digital del presupuesto por el cliente
- [ ] Módulo de gastos por obra
- [ ] App móvil React Native (API ya lista)
- [ ] Múltiples usuarios por empresa

---

## 🇨🇱 Consideraciones Chile

- Validación de RUT chileno en registro
- Precios en Pesos Chilenos (CLP) sin decimales
- Zona horaria: `America/Santiago`
- IVA configurable por presupuesto (default 0% o 19%)
- Presupuesto válido por N días (configurable)
