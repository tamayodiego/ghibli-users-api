# ghibli-users-api

API REST para la gestión de usuarios, pensada para controlar con roles el acceso a la API de Studio Ghibli. Está construida con **FastAPI**, **PostgreSQL** y **SQLAlchemy**, y la base de datos corre en **Docker**.

> **Estado actual:** el CRUD de usuarios está completo y guarda los datos en PostgreSQL. El control de acceso por roles, la integración con la API de Studio Ghibli y Redis están planeados, pero todavía no existen.

---

## Índice

- [Cómo ejecutar la aplicación](#cómo-ejecutar-la-aplicación)
- [Endpoints](#endpoints)
- [Modelos de datos](#modelos-de-datos)
- [Probar con Postman](#probar-con-postman)
- [Ver la base de datos](#ver-la-base-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Variables de entorno](#variables-de-entorno)
- [Comandos útiles](#comandos-útiles)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Licencia](#licencia)

---

## Cómo ejecutar la aplicación

### Requisitos

- [Python 3.12](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/), el gestor de dependencias y entornos de Python
- [Docker](https://www.docker.com/) con Docker Compose. En macOS sirve [OrbStack](https://orbstack.dev/) o Docker Desktop.

### 1. Clonar el repositorio e instalar dependencias

```bash
git clone https://github.com/tamayodiego/ghibli-users-api.git
cd ghibli-users-api
uv sync
```

`uv sync` crea el entorno virtual `.venv` e instala las versiones exactas de `uv.lock`.

### 2. Crear el archivo `.env`

En la raíz del proyecto, crea un archivo `.env` con la URL de conexión a la base de datos:

```env
DATABASE_URL=postgresql://ghibli:ghibli@localhost:5432/ghibli_users
```

Estos valores coinciden con los de `docker-compose.yml`. El `.env` está en el `.gitignore` y nunca se sube al repositorio.

### 3. Levantar PostgreSQL

```bash
docker compose up -d
```

Esto levanta un contenedor `ghibli-users-db` con PostgreSQL 17 en el puerto `5432`. Los datos se guardan en el volumen `pgdata`, así que no se pierden al apagar el contenedor.

Para comprobar que ya acepta conexiones:

```bash
docker exec ghibli-users-db pg_isready -U ghibli
```

### 4. Ejecutar la API

```bash
uv run uvicorn app.main:app --reload
```

- La API queda disponible en `http://127.0.0.1:8000`.
- `--reload` reinicia el servidor cada vez que guardas un archivo.
- Al arrancar, la app crea las tablas que no existan (por ejemplo `users`).
- En consola verás las consultas SQL que se ejecutan, porque el engine tiene `echo=True`.

### 5. Comprobar que funciona

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

FastAPI también genera documentación interactiva, desde donde puedes probar cada endpoint:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

> **¿El puerto 8000 está ocupado?** Usa otro con `--port 8001` y cambia la URL en consecuencia.

---

## Endpoints

### Resumen

| Método   | Ruta               | Descripción                         | Respuesta exitosa         |
|----------|--------------------|-------------------------------------|---------------------------|
| `GET`    | `/health`          | Comprueba que la API está viva      | `200` `{"status": "ok"}`  |
| `POST`   | `/users/`          | Crea un usuario                     | `201` `UserResponse`      |
| `GET`    | `/users/`          | Lista usuarios con paginación       | `200` `PaginatedUsers`    |
| `GET`    | `/users/{user_id}` | Obtiene un usuario por id           | `200` `UserResponse`      |
| `PUT`    | `/users/{user_id}` | Reemplaza todos los datos del usuario | `200` `UserResponse`    |
| `PATCH`  | `/users/{user_id}` | Actualiza solo los campos enviados  | `200` `UserResponse`      |
| `DELETE` | `/users/{user_id}` | Borra un usuario                    | `204` sin cuerpo          |
| `DELETE` | `/users/`          | Borra varios usuarios               | `200` `UserDeleteResponse` |

Si el body o los parámetros no cumplen con el schema (falta un campo obligatorio, un tipo incorrecto, `limit` fuera de rango, etc.), cualquier endpoint responde **`422 Unprocessable Entity`** con el detalle del error.

---

### `GET /health`

Comprueba que la API está levantada. No consulta la base de datos.

**Respuesta `200`:**
```json
{ "status": "ok" }
```

---

### `POST /users/`

Crea un usuario nuevo. El `id` lo asigna la base de datos.

**Body (`UserCreate`):**

| Campo  | Tipo     | Obligatorio | Descripción        |
|--------|----------|-------------|--------------------|
| `name` | `string` | Sí          | Nombre del usuario |
| `rol`  | `string` | Sí          | Rol del usuario    |

```json
{
  "name": "Totoro",
  "rol": "admin"
}
```

**Respuesta `201` (`UserResponse`):**
```json
{
  "name": "Totoro",
  "rol": "admin",
  "id": 1
}
```

---

### `GET /users/`

Lista los usuarios ordenados por `id`, con paginación. La paginación se hace en SQL (`OFFSET` / `LIMIT`), así que solo se traen de la base los registros de la página pedida.

**Query params:**

| Parámetro | Tipo  | Default | Reglas      | Descripción                         |
|-----------|-------|---------|-------------|-------------------------------------|
| `skip`    | `int` | `0`     | `>= 0`      | Cuántos usuarios saltarse           |
| `limit`   | `int` | `10`    | `1` a `100` | Cuántos usuarios devolver como máximo |

**Ejemplo:** `GET /users/?skip=0&limit=10`

**Respuesta `200` (`PaginatedUsers`):**
```json
{
  "total": 2,
  "skip": 0,
  "limit": 10,
  "data": [
    { "name": "Totoro", "rol": "admin", "id": 1 },
    { "name": "Chihiro", "rol": "user", "id": 2 }
  ]
}
```

`total` es el número total de usuarios en la base, no solo los de esta página. Sirve para calcular cuántas páginas hay.

---

### `GET /users/{user_id}`

Obtiene un usuario por su id.

**Path params:**

| Parámetro | Tipo  | Descripción    |
|-----------|-------|----------------|
| `user_id` | `int` | Id del usuario |

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Totoro", "rol": "admin", "id": 1 }
```

> ⚠️ Si el usuario no existe, hoy responde `500`. Ver [Limitaciones conocidas](#limitaciones-conocidas).

---

### `PUT /users/{user_id}`

Reemplaza **todos** los datos del usuario. Hay que mandar todos los campos.

**Path params:** `user_id` (`int`)

**Body (`UserUpdate`):**

| Campo  | Tipo     | Obligatorio |
|--------|----------|-------------|
| `name` | `string` | Sí          |
| `rol`  | `string` | Sí          |

```json
{
  "name": "Chihiro",
  "rol": "user"
}
```

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Chihiro", "rol": "user", "id": 1 }
```

> ⚠️ Si el usuario no existe, hoy responde `500`. Ver [Limitaciones conocidas](#limitaciones-conocidas).

---

### `PATCH /users/{user_id}`

Actualiza **solo los campos que mandes** en el body. Los demás quedan como estaban.

**Path params:** `user_id` (`int`)

**Body (`UserPatch`):** todos los campos son opcionales.

| Campo  | Tipo     | Obligatorio |
|--------|----------|-------------|
| `name` | `string` | No          |
| `rol`  | `string` | No          |

```json
{ "rol": "admin" }
```

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Chihiro", "rol": "admin", "id": 1 }
```

> ⚠️ Si el usuario no existe, hoy responde `200` con `null`. Ver [Limitaciones conocidas](#limitaciones-conocidas).

---

### `DELETE /users/{user_id}`

Borra un usuario por su id.

**Path params:** `user_id` (`int`)

**Respuesta `204 No Content`:** sin cuerpo.

> ⚠️ Responde `204` aunque el usuario no exista. Ver [Limitaciones conocidas](#limitaciones-conocidas).

---

### `DELETE /users/`

Borra varios usuarios a la vez y dice cuáles se borraron y cuáles no existían.

**Body (`UserDelete`):**

| Campo   | Tipo        | Obligatorio | Descripción          |
|---------|-------------|-------------|----------------------|
| `users` | `list[int]` | Sí          | Ids de los usuarios a borrar |

```json
{ "users": [1, 2, 50] }
```

**Respuesta `200` (`UserDeleteResponse`):**
```json
{
  "users_deleted": [1, 2],
  "users_dont_deleted": [50]
}
```

- `users_deleted`: ids que existían y se borraron.
- `users_dont_deleted`: ids que no existían en la base.

> En Postman, el body de un `DELETE` se manda igual que en un `POST`: pestaña **Body** → **raw** → **JSON**.

---

## Modelos de datos

### Tabla `users` (modelo SQLAlchemy `User`)

| Columna | Tipo                | Restricciones                    |
|---------|---------------------|----------------------------------|
| `id`    | `integer`           | Llave primaria, autoincremental  |
| `name`  | `character varying` | `NOT NULL`                       |
| `rol`   | `character varying` | `NOT NULL`                       |

### Schemas de Pydantic

Definidos en `app/modules/users/schemas.py`. Son lo que entra y sale de la API; nunca se expone el modelo de base de datos directamente.

| Schema               | Uso                              | Campos                                                   |
|----------------------|----------------------------------|----------------------------------------------------------|
| `UserCreate`         | Body de `POST /users/`           | `name: str`, `rol: str`                                  |
| `UserResponse`       | Respuesta con un usuario         | `id: int`, `name: str`, `rol: str`                       |
| `UserUpdate`         | Body de `PUT`                    | `name: str`, `rol: str`                                  |
| `UserPatch`          | Body de `PATCH`                  | `name: str \| None`, `rol: str \| None`                  |
| `PaginatedUsers`     | Respuesta de `GET /users/`       | `total: int`, `skip: int`, `limit: int`, `data: list[UserResponse]` |
| `UserDelete`         | Body de `DELETE /users/`         | `users: list[int]`                                       |
| `UserDeleteResponse` | Respuesta de `DELETE /users/`    | `users_deleted: list[int]`, `users_dont_deleted: list[int]` |

---

## Probar con Postman

En `postman/ghibli-users-api.postman_collection.json` hay una colección con todos los endpoints.

1. En Postman, dale a **Import** y arrastra el archivo.
2. Corre primero **Crear usuario**. Su script guarda el `id` de la respuesta en la variable `userId`.
3. Los demás requests (obtener, PUT, PATCH, borrar) usan `{{userId}}` automáticamente.

La colección tiene dos variables, que puedes editar en la pestaña **Variables**:

| Variable  | Valor por defecto       |
|-----------|-------------------------|
| `baseUrl` | `http://127.0.0.1:8000` |
| `userId`  | `1`                     |

---

## Ver la base de datos

Con estos datos de conexión puedes usar cualquier cliente de PostgreSQL:

| Campo      | Valor          |
|------------|----------------|
| Host       | `localhost`    |
| Puerto     | `5432`         |
| Usuario    | `ghibli`       |
| Contraseña | `ghibli`       |
| Base       | `ghibli_users` |

Algunas opciones:

- **VS Code:** la extensión *Database Client* (de Weijan Chen).
- **macOS:** [TablePlus](https://tableplus.com/).
- **Terminal**, sin instalar nada:
  ```bash
  docker exec -it ghibli-users-db psql -U ghibli -d ghibli_users -c 'SELECT * FROM users;'
  ```

---

## Estructura del proyecto

```
ghibli-users-api/
├── app/
│   ├── main.py                  # Crea la app FastAPI, registra routers y crea las tablas
│   ├── database.py              # Engine, SessionLocal, Base y get_db
│   └── modules/
│       └── users/
│           ├── routers.py       # Endpoints HTTP de /users
│           ├── service.py       # Lógica de negocio
│           ├── repository.py    # Acceso a datos con SQLAlchemy
│           ├── models.py        # Modelo de base de datos (tabla users)
│           └── schemas.py       # Schemas de Pydantic (entrada/salida de la API)
├── postman/                     # Colección de Postman
├── tests/
├── docker-compose.yml           # PostgreSQL para desarrollo local
├── pyproject.toml               # Dependencias del proyecto
└── uv.lock                      # Versiones exactas de las dependencias
```

### Arquitectura por capas

Cada módulo (por ahora solo `users`) se divide en tres capas. Cada una solo habla con la de abajo:

```
Request HTTP
    │
    ▼
routers.py     → recibe y valida el request, llama al service y devuelve la respuesta
    │
    ▼
service.py     → lógica de negocio (por ejemplo: PUT reemplaza todo, PATCH solo lo enviado)
    │
    ▼
repository.py  → convierte schemas ↔ modelos y habla con la base de datos
    │
    ▼
PostgreSQL
```

- **El router** no sabe nada de SQLAlchemy: solo trabaja con schemas y con el service.
- **El service** tampoco ve modelos de base de datos: recibe y devuelve schemas.
- **El repository** es la única capa que toca los modelos y la sesión de SQLAlchemy.

### Sesión de base de datos por request

Cada endpoint recibe su propio `UserService` mediante `Depends`:

```python
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
```

En cada request, FastAPI llama a `get_db`, que abre una sesión. Con esa sesión crea el `UserService`, se lo pasa al endpoint y, al terminar el request, cierra la sesión.

---

## Variables de entorno

| Variable       | Obligatoria | Descripción                          | Ejemplo                                                  |
|----------------|-------------|--------------------------------------|----------------------------------------------------------|
| `DATABASE_URL` | Sí          | URL de conexión a PostgreSQL         | `postgresql://ghibli:ghibli@localhost:5432/ghibli_users` |

Se leen del archivo `.env` con `python-dotenv`. Si falta `DATABASE_URL`, la app no arranca.

---

## Comandos útiles

```bash
# Instalar o actualizar dependencias
uv sync

# Agregar una dependencia nueva
uv add <paquete>

# Levantar la API
uv run uvicorn app.main:app --reload

# Levantar / apagar PostgreSQL
docker compose up -d
docker compose down

# Ver los logs de PostgreSQL
docker compose logs -f db

# Borrar la base de datos por completo (¡elimina todos los datos!)
docker compose down -v
```

---

## Limitaciones conocidas

Cosas que todavía no funcionan como deberían:

- **Usuario que no existe:** varios endpoints no responden `404`.
  - `GET /users/{user_id}` y `PUT /users/{user_id}` responden `500`.
  - `PATCH /users/{user_id}` responde `200` con `null`.
  - `DELETE /users/{user_id}` responde `204` aunque no se haya borrado nada.
- **Roles:** `rol` acepta cualquier texto. Todavía no hay una lista de roles válidos ni control de acceso.
- **Tablas:** se crean al arrancar con `Base.metadata.create_all`. Esto no modifica tablas que ya existen; para cambios de esquema harán falta migraciones (por ejemplo con Alembic).
- **Tests:** la carpeta `tests/` todavía no tiene pruebas.

---

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).
