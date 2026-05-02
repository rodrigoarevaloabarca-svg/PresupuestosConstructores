# Constructor Express — API REST

**Base URL:** `https://constructorexpress.cl/api/v1`
**Autenticacion:** JWT Bearer token en header `Authorization: Bearer <token>`
**Formato de datos:** JSON
**Throttling:** 1.000 req/hora (autenticado) · 100 req/hora (anonimo)
**Paginacion:** `?page=N` — 20 resultados por pagina

> **Swagger UI interactivo:** `/api/v1/docs/`
> **Schema OpenAPI (JSON):** `/api/v1/schema/`

---

## Indice

- [Autenticacion JWT](#autenticacion-jwt)
- [Dashboard](#dashboard)
- [Presupuestos](#presupuestos)
- [Clientes](#clientes)
- [Productos (catalogo propio)](#productos-catalogo-propio)
- [Sugerencias (autocomplete)](#sugerencias-autocomplete)
- [Calculadora de materiales](#calculadora-de-materiales)
- [Webhooks](#webhooks)
- [Codigos de estado](#codigos-de-estado)
- [Multi-tenancy](#multi-tenancy)
- [Versionado de presupuestos](#versionado-de-presupuestos)
- [Firma digital](#firma-digital)
- [Clientes SDK](#clientes-sdk)

---

## Autenticacion JWT

### Obtener tokens

```
POST /api/v1/auth/token/
```

**Body:**
```json
{
  "email": "demo@constructorexpress.cl", # pragma: allowlist secret
  "password": "Demo1234!" # pragma: allowlist secret
}
```

**Respuesta 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "contractor_id": 1,
  "email": "demo@constructorexpress.cl",
  "is_pro": false
}
```

| Campo | Descripcion |
|-------|-------------|
| `access` | Token de acceso — incluir en cada request como `Authorization: Bearer <access>` |
| `refresh` | Token de renovacion — usar para obtener un nuevo `access` |
| `contractor_id` | ID del contratista autenticado |
| `is_pro` | `true` si el usuario tiene plan Pro activo |

El token `access` expira en **1 hora**. El `refresh` expira en **7 dias**.

```bash
# Ejemplo con curl
curl -X POST https://constructorexpress.cl/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "tu@email.cl", "password": "tu-contrasena"}' # pragma: allowlist secret
```

---

### Renovar access token

```
POST /api/v1/auth/refresh/
```

**Body:**
```json
{ "refresh": "<refresh_token>" }
```

**Respuesta 200:**
```json
{ "access": "<nuevo_access_token>" }
```

---

### Revocar refresh token (logout API)

```
POST /api/v1/auth/blacklist/
```

**Body:**
```json
{ "refresh": "<refresh_token>" }
```

**Respuesta 205:** `{}`

Despues de revocar, el `refresh` queda en blacklist y no puede usarse para renovar el `access`.

---

### Usar el token en cada request

```bash
curl https://constructorexpress.cl/api/v1/presupuestos/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Dashboard

### Estadisticas generales

```
GET /api/v1/stats/
```

**Respuesta 200:**
```json
{
  "total_clients": 8,
  "total_products": 15,
  "total_budgets": 23,
  "budgets_this_month": 4,
  "accepted_budgets": 14,
  "pending_budgets": 5,
  "total_revenue": 4850000,
  "pending_revenue": 980000,
  "conversion_rate": 60.9
}
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `total_revenue` | int (CLP) | Suma de presupuestos aceptados |
| `pending_revenue` | int (CLP) | Suma de presupuestos en estado `enviado` |
| `conversion_rate` | float (%) | `aceptados / total * 100` |

---

## Presupuestos

### Listar presupuestos

```
GET /api/v1/presupuestos/
GET /api/v1/presupuestos/?status=enviado
GET /api/v1/presupuestos/?status=borrador&page=2
```

**Parametros de query:**

| Parametro | Valores posibles | Descripcion |
|-----------|-----------------|-------------|
| `status` | `borrador` `enviado` `aceptado` `rechazado` `vencido` | Filtrar por estado |
| `page` | int | Pagina de resultados (20 por pagina) |

**Respuesta 200:**
```json
{
  "count": 23,
  "next": "https://constructorexpress.cl/api/v1/presupuestos/?page=2",
  "previous": null,
  "results": [
    {
      "id": 7,
      "number": 7,
      "version": 1,
      "title": "Reparacion bano — Las Rosas",
      "client_name": "Maria Gonzalez",
      "status": "enviado",
      "status_display": "Enviado al Cliente",
      "total": 300523,
      "created_at": "2026-04-10T14:32:00Z"
    }
  ]
}
```

---

### Detalle de presupuesto (lectura)

```
GET /api/v1/presupuestos/{id}/
```

**Respuesta 200:**
```json
{
  "id": 7,
  "number": 7,
  "version": 1,
  "parent": null,
  "title": "Reparacion bano — Las Rosas",
  "client_name": "Maria Gonzalez",
  "status": "enviado",
  "status_display": "Enviado al Cliente",
  "tax_percent": "19.00",
  "subtotal_materials": 122700,
  "subtotal_labor": 130000,
  "subtotal": 252700,
  "tax_amount": 47973,
  "total": 300673,
  "validity_days": 15,
  "valid_until": "2026-04-25",
  "payment_terms": "50% anticipo, 50% a la entrega",
  "notes": "Incluye materiales y mano de obra",
  "created_at": "2026-04-10T14:32:00Z",
  "sent_at": "2026-04-11T09:00:00Z",
  "material_items": [
    {
      "id": 12,
      "name": "Griferia mezcladora monocomando",
      "unit": "un",
      "unit_display": "Unidad",
      "quantity": "1.00",
      "unit_price": 45000,
      "total": 45000
    }
  ],
  "labor_items": [
    {
      "id": 8,
      "name": "Instalacion completa de bano",
      "unit": "gl",
      "unit_display": "Global",
      "quantity": "1.00",
      "unit_price": 130000,
      "total": 130000
    }
  ]
}
```

---

### CRUD completo de presupuestos

El ViewSet de escritura permite crear y modificar presupuestos **incluyendo sus items** en una sola request.

#### Listar con CRUD

```
GET  /api/v1/presupuestos/write/
```

#### Crear presupuesto

```
POST /api/v1/presupuestos/write/
```

**Body:**
```json
{
  "client": 3,
  "title": "Instalacion electrica bodega",
  "tax_percent": "19.00",
  "validity_days": 15,
  "payment_terms": "50% anticipo, 50% a la entrega",
  "notes": "Incluye materiales y mano de obra",
  "material_items": [
    {
      "name": "Cable 2.5mm THHN",
      "unit": "ml",
      "quantity": "50.00",
      "unit_price": 890
    },
    {
      "name": "Caja derivacion",
      "unit": "un",
      "quantity": "3.00",
      "unit_price": 2200
    }
  ],
  "labor_items": [
    {
      "name": "Mano de obra electrica",
      "unit": "gl",
      "quantity": "1.00",
      "unit_price": 180000
    }
  ]
}
```

**Respuesta 201:** el presupuesto creado en formato detalle.

> El `number` se asigna automaticamente (secuencial por contratista). No incluirlo en el body.

#### Actualizar / eliminar

```
GET    /api/v1/presupuestos/write/{id}/
PUT    /api/v1/presupuestos/write/{id}/
PATCH  /api/v1/presupuestos/write/{id}/
DELETE /api/v1/presupuestos/write/{id}/
```

Un `PUT` o `PATCH` sobre un presupuesto en estado `enviado`, `aceptado` o `rechazado` crea automaticamente una nueva version (ver [Versionado de presupuestos](#versionado-de-presupuestos)).

**Errores comunes:**

| Codigo | Motivo |
|--------|--------|
| `400` | Datos invalidos (cliente no existe, precio negativo, etc.) |
| `403` | Sin permisos o limite del plan gratuito alcanzado |
| `404` | Presupuesto no encontrado o pertenece a otro contratista |

---

## Clientes

### Listar / crear

```
GET  /api/v1/clientes/
GET  /api/v1/clientes/?page=2
POST /api/v1/clientes/
```

**Body de creacion:**
```json
{
  "name": "Pedro Soto Construcciones",
  "rut": "12.345.678-9",
  "phone": "+56912345678",
  "email": "pedro@soto.cl",
  "address": "Av. Apoquindo 1234, Las Condes",
  "city": "Santiago",
  "notes": "Referido por Maria Gonzalez"
}
```

**Respuesta 201:**
```json
{
  "id": 9,
  "name": "Pedro Soto Construcciones",
  "rut": "12.345.678-9",
  "phone": "+56912345678",
  "email": "pedro@soto.cl",
  "address": "Av. Apoquindo 1234, Las Condes",
  "city": "Santiago",
  "notes": "Referido por Maria Gonzalez",
  "budget_count": 0,
  "created_at": "2026-04-18T10:00:00Z"
}
```

> `403` si el plan gratuito ya tiene 10 clientes.

### Detalle / editar / eliminar

```
GET    /api/v1/clientes/{id}/
PUT    /api/v1/clientes/{id}/
PATCH  /api/v1/clientes/{id}/
DELETE /api/v1/clientes/{id}/
```

---

## Productos (catalogo propio)

### Listar / buscar / crear

```
GET  /api/v1/productos/
GET  /api/v1/productos/?q=cemento
POST /api/v1/productos/
```

**Parametros de query:**

| Parametro | Descripcion |
|-----------|-------------|
| `q` | Busqueda por nombre (`icontains`) |

**Body de creacion:**
```json
{
  "name": "Cemento Portland 25kg",
  "description": "Bolsa de 25kg marca Melon",
  "category": "materiales",
  "unit": "bls",
  "cost_price": 4200,
  "sale_price": 5500,
  "sku": "CEM-025"
}
```

**Categorias disponibles:**

| Valor | Descripcion |
|-------|-------------|
| `materiales` | Materiales de construccion |
| `herramientas` | Herramientas |
| `electricidad` | Materiales electricos |
| `gasfiteria` | Materiales de gasfiteria |
| `ceramica` | Ceramica y baldosas |
| `pintura` | Pintura y accesorios |
| `madera` | Maderas y tableros |
| `otro` | Otros |

**Unidades disponibles:**

| Valor | Descripcion |
|-------|-------------|
| `un` | Unidad |
| `m2` | Metro cuadrado |
| `m3` | Metro cubico |
| `ml` | Metro lineal |
| `kg` | Kilogramo |
| `lt` | Litro |
| `hr` | Hora |
| `gl` | Global |
| `bls` | Bolsa |
| `pk` | Pack |

> `403` si el plan gratuito ya tiene 20 productos.

### Detalle / editar / eliminar

```
GET    /api/v1/productos/{id}/
PUT    /api/v1/productos/{id}/
PATCH  /api/v1/productos/{id}/
DELETE /api/v1/productos/{id}/
```

---

## Sugerencias (autocomplete)

Endpoint de autocompletado que combina el catalogo propio del contratista (prioridad) con precios de ferreterias externas (Sodimac, Easy, Imperial).

```
GET /api/v1/productos/sugerencias/?q=cemento
GET /api/v1/productos/sugerencias/?q=cemento&limit=8
```

**Throttle:** 60 req/min por usuario.

**Parametros de query:**

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `q` | string | — | Termino de busqueda (minimo 3 caracteres) |
| `limit` | int | 10 | Maximo de resultados (tope: 20) |

Si `q` tiene 2 caracteres o menos, retorna `[]` directamente sin consultar la BD.

**Respuesta 200:**
```json
[
  {
    "source": "catalog",
    "name": "Cemento Especial 25kg",
    "price": 4800,
    "unit": "bls"
  },
  {
    "source": "sodimac",
    "name": "Cemento Portland 25kg Melon",
    "price": 4990,
    "url": "https://www.sodimac.com/sodimac-cl/product/..."
  },
  {
    "source": "easy",
    "name": "Cemento Melon 25kg",
    "price": 5290,
    "url": "https://www.easy.cl/..."
  },
  {
    "source": "imperial",
    "name": "Cemento 25kg Imperial",
    "price": 4750,
    "url": "https://www.imperial.cl/..."
  }
]
```

**Campos por fuente:**

| Campo | `catalog` | `sodimac` / `easy` / `imperial` |
|-------|:---------:|:-------------------------------:|
| `source` | `"catalog"` | nombre del retailer |
| `name` | Si | Si |
| `price` | precio venta (CLP) | precio de referencia (CLP) |
| `unit` | Si | No |
| `url` | No | Si |

> Los precios de ferreteria son de **referencia**. El maestro debe ajustar su margen antes de usarlos en el presupuesto.

Los resultados de ferreteria provienen del caché semanal (`RetailerProduct`). Se actualizan cada domingo a las 3 AM via Celery Beat.

---

## Calculadora de materiales

Retorna las recetas personalizadas del contratista autenticado para su uso en la calculadora de materiales (modal del formulario de presupuesto y pagina standalone).

```
GET /api/v1/calculadora/recetas/
```

**No requiere parametros.**

**Respuesta 200:**
```json
[
  {
    "id": 3,
    "name": "Pintura de cielo interior",
    "rubro": "Pintura",
    "icon": "🎨",
    "input_label": "Superficie a pintar",
    "input_unit": "m²",
    "input_placeholder": "Ej: 30",
    "items": [
      { "name": "Pintura latex cielo", "unit": "lt", "factor": "0.2500" },
      { "name": "Lija N°120", "unit": "un", "factor": "0.5000" }
    ]
  }
]
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | int | ID de la receta |
| `name` | string | Nombre de la receta |
| `rubro` | string | Categoria (Pintura, Ceramica, Pisos, etc.) |
| `icon` | string | Emoji del icono |
| `input_label` | string | Etiqueta de la medida de entrada |
| `input_unit` | string | Unidad de la medida de entrada (m², ml, m³, etc.) |
| `input_placeholder` | string | Placeholder sugerido para el input (puede estar vacio) |
| `items[].factor` | string | Cantidad de material por cada unidad de medida ingresada |

Retorna solo las recetas activas (`is_active=True`) del contratista autenticado. Si no tiene recetas personalizadas, retorna `[]`. Las recetas predefinidas (9 incorporadas) estan hardcodeadas en `calculadora.js` y no se sirven por esta API.

**CRUD de recetas** (solo via interfaz web):

| Metodo | URL | Descripcion |
|--------|-----|-------------|
| GET | `/presupuestos/calculadora/recetas/` | Listar recetas del contratista |
| GET/POST | `/presupuestos/calculadora/recetas/crear/` | Crear nueva receta |
| GET/POST | `/presupuestos/calculadora/recetas/<id>/editar/` | Editar receta existente |
| POST | `/presupuestos/calculadora/recetas/<id>/eliminar/` | Eliminar receta |

---

## Webhooks

### MercadoPago

```
POST /api/webhooks/mercadopago/
```

Recibe notificaciones de pago de MercadoPago. Valida la firma HMAC con `MP_WEBHOOK_SECRET`. **No requiere autenticacion JWT.**

Al recibir una notificacion de pago exitosa, activa automaticamente el plan Pro del contratista correspondiente.

---

## Codigos de estado

| Codigo | Significado |
|--------|-------------|
| `200` | OK |
| `201` | Recurso creado exitosamente |
| `204` | Eliminado (sin contenido en respuesta) |
| `205` | Operacion exitosa sin contenido (ej: blacklist) |
| `400` | Request invalida — ver campo `detail` o errores por campo |
| `401` | No autenticado — token faltante o expirado |
| `403` | Sin permisos o limite del plan gratuito alcanzado |
| `404` | Recurso no encontrado o pertenece a otro contratista |
| `429` | Throttle excedido |

**Formato de error estandar:**
```json
{
  "detail": "No se encontro el recurso."
}
```

**Formato de error de validacion:**
```json
{
  "material_items": [
    {
      "unit_price": ["Este campo es obligatorio."]
    }
  ],
  "client": ["Este campo no puede ser nulo."]
}
```

---

## Multi-tenancy

Todos los recursos estan **aislados por contratista**. Un token JWT solo permite acceder y modificar los datos del contratista autenticado. El backend filtra siempre por `contractor=request.user`.

Intentar acceder a un recurso de otro contratista devuelve `404`, no `403`, para no revelar la existencia del recurso.

---

## Versionado de presupuestos

Cuando se edita un presupuesto en estado `enviado`, `aceptado` o `rechazado`, el sistema **crea automaticamente una nueva version** (v2, v3...) en estado `borrador`, preservando el original intacto.

**Ejemplo — presupuesto #7 editado mientras esta enviado:**
```json
{
  "id": 12,
  "number": 7,
  "version": 2,
  "parent": 7,
  "status": "borrador",
  ...
}
```

`number` identifica el presupuesto (constante en todas las versiones). `version` identifica la revision. `parent` apunta al `id` de la version anterior.

Los presupuestos en estado `borrador` se editan directamente sin crear version nueva.

---

## Firma digital

La firma digital ocurre en la **vista publica HTML**, no via API REST. Flujo:

1. El contratista genera un link publico: `GET /presupuestos/{id}/link/`
2. El cliente abre `/presupuestos/ver/<token>/` sin necesidad de cuenta
3. Si el presupuesto esta en estado `enviado`, el cliente ve el canvas de firma
4. El cliente firma y hace POST a `/presupuestos/ver/<token>/firmar/` (rate limit: 3/hora por IP)
5. El sistema guarda la firma como PNG + SHA-256 + IP + user-agent
6. El presupuesto pasa automaticamente a `aceptado`

Los tokens de link publico expiran a los 30 dias y pueden revocarse manualmente.

---

## Clientes SDK

### Python (httpx)

```python
import httpx

BASE = "https://constructorexpress.cl/api/v1"

def get_token(email: str, password: str) -> str:
    r = httpx.post(f"{BASE}/auth/token/", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access"]

token = get_token("demo@constructorexpress.cl", "Demo1234!")
headers = {"Authorization": f"Bearer {token}"}

# Listar presupuestos enviados
presupuestos = httpx.get(
    f"{BASE}/presupuestos/",
    headers=headers,
    params={"status": "enviado"}
).json()

# Crear presupuesto
nuevo = httpx.post(
    f"{BASE}/presupuestos/write/",
    headers=headers,
    json={
        "client": 1,
        "title": "Instalacion bano",
        "tax_percent": "19.00",
        "validity_days": 15,
        "material_items": [
            {"name": "Griferia monocomando", "unit": "un", "quantity": "1.00", "unit_price": 45000}
        ],
        "labor_items": [
            {"name": "Instalacion", "unit": "gl", "quantity": "1.00", "unit_price": 80000}
        ]
    }
).json()

print(f"Presupuesto #{nuevo['number']} creado. Total: ${nuevo['total']:,}")
```

### JavaScript / Node.js

```javascript
const BASE = 'https://constructorexpress.cl/api/v1';

async function getToken(email, password) {
  const res = await fetch(`${BASE}/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Auth fallida: ${res.status}`);
  return (await res.json()).access;
}

const token = await getToken('demo@constructorexpress.cl', 'Demo1234!');
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
};

// Listar clientes
const clientes = await fetch(`${BASE}/clientes/`, { headers }).then(r => r.json());
console.log(`${clientes.count} clientes encontrados`);

// Autocompletado de materiales
const sugerencias = await fetch(
  `${BASE}/productos/sugerencias/?q=cemento&limit=5`,
  { headers }
).then(r => r.json());

sugerencias.forEach(s => {
  const origen = s.source === 'catalog' ? 'Mi catalogo' : s.source;
  console.log(`[${origen}] ${s.name} — $${s.price.toLocaleString('es-CL')}`);
});
```

### curl (referencia rapida)

```bash
BASE="https://constructorexpress.cl/api/v1"

# Obtener token
TOKEN=$(curl -s -X POST "$BASE/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@constructorexpress.cl","password":"Demo1234!"}' \ # pragma: allowlist secret
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# Listar presupuestos
curl -s "$BASE/presupuestos/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Ver sugerencias
curl -s "$BASE/productos/sugerencias/?q=griferia" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```
