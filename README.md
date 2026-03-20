# Cremas Inventory API

API para gestionar el inventario de un negocio de cremas (paletas de leche).

## Características

- **Gestión de inventario**: Agregar, actualizar y eliminar cremas/sabores
- **Registro de ventas**: Las ventas descuetan stock automáticamente
- **Apartados/Reservas**: Apartar cremas para clientes con fecha de entrega
- **Alertas de stock**: Notificaciones cuando el stock está bajo (≤3 unidades)
- **Historial**: Registro completo de ventas y reservas por sabor

## Tech Stack

- **FastAPI** - Framework web
- **PostgreSQL** - Base de datos (Supabase)
- **SQLAlchemy 2.0** - ORM async
- **Pydantic v2** - Validación de datos

## Arquitectura

```
src/
├── domain/           # Entidades y lógica de negocio
│   ├── entities/      # Cream, Sale, Reservation
│   └── repositories.py
│
├── application/       # Casos de uso
│   ├── services/      # InventoryService, ReservationService, NotificationService
│   └── dtos/          # Data Transfer Objects
│
├── infrastructure/    # Implementaciones externas
│   ├── database/     # SQLAlchemy models y repositorios
│   ├── config/       # Settings (pydantic-settings)
│   └── auth.py       # JWT verification y auth middleware
│
└── api/              # Endpoints FastAPI
    └── routes/
```

## Instalación

1. **Clonar el repositorio**

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Edita el archivo `.env` con tus credenciales:
- `DATABASE_URL`: URL de PostgreSQL/Supabase
- `SUPABASE_URL` y `SUPABASE_ANON_KEY`
- `GMAIL_*`: Credenciales de Google Cloud para notificaciones

5. **Iniciar la API**

```bash
python main.py
```

O con uvicorn:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Cremas

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/creams` | Listar todas las cremas |
| POST | `/creams` | Crear nueva crema |
| GET | `/creams/{id}` | Obtener crema por ID |
| PUT | `/creams/{id}` | Actualizar cantidad |
| POST | `/creams/{id}/add-stock` | Agregar stock |
| DELETE | `/creams/{id}` | Eliminar crema |

### Ventas

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/creams/{id}/sell` | Registrar venta |
| GET | `/creams/{id}/sales` | Historial de ventas |

### Reservas

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/creams/{id}/reserve` | Crear reserva |
| POST | `/creams/{id}/reserve/activate` | Reactivar reserva |
| GET | `/creams/reservations/active` | Ver reservas activas |
| POST | `/creams/reservations/{id}/deliver` | Entregar reserva |
| POST | `/creams/reservations/{id}/cancel` | Cancelar reserva |

### Alertas

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/creams/low-stock` | Cremas con stock bajo |

### Historial

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/creams/{id}/history` | Historial completo |

## Seguridad

### Variables de Entorno

NUNCA guardes credenciales reales en el código. Usa el archivo `.env`:

1. Copia `.env.example` a `.env`
2. Completa con tus credenciales reales
3. `.env` está en `.gitignore` - nunca se sube al repositorio

### Configuración de Seguridad

| Variable | Descripción |
|----------|-------------|
| `ENV` | `development` o `production` |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_ANON_KEY` | Key pública (segura para exponer en cliente) |
| `SUPABASE_SERVICE_ROLE_KEY` | Key privada (NUNCA exponer en frontend) |

### CORS (Cross-Origin Resource Sharing)

Los orígenes permitidos se configuran en `config.yaml`:

```yaml
app:
  allowed_origins:
    - "http://localhost:3000"      # Desarrollo
    # - "https://tu-dominio.com"    # Producción - agregar cuando esté listo
  env: development  # Cambiar a "production" en deploy
```

### Row Level Security (RLS)

Las políticas de RLS se encuentran en `supabase/migrations/001_rls_policies.sql`.

**Para aplicar las políticas RLS:**

1. Ve a [Supabase Dashboard](https://app.supabase.com) > SQL Editor
2. Copia y ejecuta el contenido de `supabase/migrations/001_rls_policies.sql`
3. Ejecuta también `supabase/migrations/002_cream_owners.sql`

**Políticas implementadas:**

| Tabla | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| `creams` | Todos los usuarios autenticados | Usuarios autenticados | Dueños (vía `cream_owners`) | Dueños |
| `sales` | Usuarios autenticados | Usuarios autenticados | - | - |
| `reservations` | Usuarios autenticados | Usuarios autenticados | Usuarios autenticados | Usuarios autenticados |

### Autenticación JWT

La API usa JWT de Supabase para autenticación:

- **Lectura pública**: GET endpoints funcionan sin token
- **Escritura protegida**: POST/PUT/DELETE requieren `Authorization: Bearer <token>`

Para probar endpoints protegidos:
```bash
curl -X POST http://localhost:8000/creams \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"flavor_name":"Vainilla","quantity":5}'
```

### Obteniendo el Service Role Key

1. Ve a Supabase Dashboard > Project Settings > API
2. Copia la "service_role key" (NO la anon key)
3. Agrégala a tu `.env` como `SUPABASE_SERVICE_ROLE_KEY`

## Deploy en Render

1. Subir código a GitHub
2. Crear nuevo servicio en Render
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
4. Añadir variables de entorno en Render dashboard
5. Desplegar

## Desarrollo

```bash
# Instalar pre-commit hooks (si hay)
pre-commit install

# Ejecutar tests
pytest

# Verificar tipos
mypy src/
```

## Licencia

MIT
