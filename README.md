# ghibli-users-api

API REST para la gestión de usuarios, pensada para controlar con roles el acceso a la API de Studio Ghibli. Está construida con **FastAPI**, **PostgreSQL**, **SQLAlchemy** y **Alembic**, y se despliega con **Docker Compose**.

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
- [Migraciones](#migraciones)
- [Comandos útiles](#comandos-útiles)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Licencia](#licencia)

---

## Cómo ejecutar la aplicación

Hay dos formas de correrla:

- **[Con Docker](#opción-a-todo-con-docker-producción):** la API y PostgreSQL corren en contenedores. Es la forma de desplegarla en un servidor.
- **[En local para desarrollar](#opción-b-desarrollo-local):** solo PostgreSQL corre en Docker y la API corre en tu máquina con recarga automática.

### Opción A: todo con Docker (producción)

**Requisitos:** [Docker](https://www.docker.com/) con Docker Compose. En macOS sirve [OrbStack](https://orbstack.dev/) o Docker Desktop. No hace falta instalar Python.

**1. Clonar el repositorio**

```bash
git clone https://github.com/tamayodiego/ghibli-users-api.git
cd ghibli-users-api
```

**2. Crear el `.env` a partir de la plantilla**

```bash
cp .env.example .env
```

Abre `.env` y cambia `POSTGRES_PASSWORD` por una contraseña real. Docker Compose lee de ahí las credenciales de la base y no arranca si falta alguna.

> ⚠️ PostgreSQL solo toma la contraseña la **primera vez** que crea el volumen de datos. Si después la cambias en el `.env`, la base sigue usando la anterior. Define la contraseña buena antes del primer `up`.

**3. Levantar todo**

```bash
docker compose up -d --build
```

Esto hace lo siguiente:

1. Construye la imagen de la API con el `Dockerfile`.
2. Levanta PostgreSQL 17 (`ghibli-users-db`) y espera a que su healthcheck diga que está listo.
3. Levanta la API (`ghibli-users-api`), que primero aplica las migraciones pendientes (`alembic upgrade head`) y después arranca uvicorn en el puerto `8000`.

Los dos contenedores tienen `restart: unless-stopped`: si se caen o se reinicia el servidor, vuelven a levantarse solos. Los datos se guardan en el volumen `pgdata`.

**4. Comprobar que funciona**

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

**Para actualizar a una versión nueva:**

```bash
git pull
docker compose up -d --build
```

La API aplica sola las migraciones nuevas al arrancar.

### Opción B: desarrollo local

**Requisitos:**

- [Python 3.12](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/), el gestor de dependencias y entornos de Python
- [Docker](https://www.docker.com/) con Docker Compose, para PostgreSQL

**1. Clonar el repositorio e instalar dependencias**

```bash
git clone https://github.com/tamayodiego/ghibli-users-api.git
cd ghibli-users-api
uv sync
```

`uv sync` crea el entorno virtual `.venv` e instala las versiones exactas de `uv.lock`.

**2. Crear el `.env`**

```bash
cp .env.example .env
```

Revisa que la contraseña de `DATABASE_URL` sea la misma que `POSTGRES_PASSWORD`. Si quieres ver en consola las consultas SQL, deja `SQL_ECHO=true`.

**3. Levantar solo PostgreSQL**

```bash
docker compose up -d db
```

El puerto `5432` solo se publica en `127.0.0.1`, así que la base es accesible desde tu máquina, pero no desde afuera.

**4. Aplicar las migraciones**

```bash
uv run alembic upgrade head
```

Crea la tabla `users` y cualquier cambio de esquema pendiente.

**5. Ejecutar la API**

```bash
uv run uvicorn app.main:app --reload
```

`--reload` reinicia el servidor cada vez que guardas un archivo.

> Si ya tienes corriendo el contenedor `api` de la opción A, apágalo con `docker compose stop api`, porque los dos usan el puerto `8000`.

### Documentación interactiva

Con la API corriendo, de cualquiera de las dos formas, FastAPI genera documentación desde donde puedes probar cada endpoint:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

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

Con estos datos de conexión puedes usar cualquier cliente de PostgreSQL. Usuario, contraseña y base son los de tu `.env`:

| Campo      | Valor                                   |
|------------|-----------------------------------------|
| Host       | `localhost`                             |
| Puerto     | `5432`                                  |
| Usuario    | `POSTGRES_USER` (por defecto `ghibli`)  |
| Contraseña | `POSTGRES_PASSWORD`                     |
| Base       | `POSTGRES_DB` (por defecto `ghibli_users`) |

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
│   ├── main.py                  # Crea la app FastAPI y registra los routers
│   ├── database.py              # Engine, SessionLocal, Base y get_db
│   └── modules/
│       └── users/
│           ├── routers.py       # Endpoints HTTP de /users
│           ├── service.py       # Lógica de negocio
│           ├── repository.py    # Acceso a datos con SQLAlchemy
│           ├── models.py        # Modelo de base de datos (tabla users)
│           └── schemas.py       # Schemas de Pydantic (entrada/salida de la API)
├── migrations/
│   ├── env.py                   # Configuración de Alembic (lee DATABASE_URL y Base.metadata)
│   └── versions/                # Migraciones numeradas: 0001_create_users.py, ...
├── postman/                     # Colección de Postman
├── tests/
├── alembic.ini                  # Configuración de Alembic
├── Dockerfile                   # Imagen de la API
├── docker-compose.yml           # API + PostgreSQL
├── .env.example                 # Plantilla de variables de entorno
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

Se definen en el archivo `.env`; `.env.example` es la plantilla.

| Variable            | Obligatoria | Usada por                  | Descripción                                          | Ejemplo                                                  |
|---------------------|-------------|----------------------------|------------------------------------------------------|----------------------------------------------------------|
| `POSTGRES_USER`     | Sí          | Docker Compose             | Usuario de PostgreSQL                                | `ghibli`                                                 |
| `POSTGRES_PASSWORD` | Sí          | Docker Compose             | Contraseña de PostgreSQL                             | `una-contraseña-segura`                                  |
| `POSTGRES_DB`       | Sí          | Docker Compose             | Nombre de la base de datos                           | `ghibli_users`                                           |
| `DATABASE_URL`      | Solo local  | La API fuera de Docker y Alembic | URL de conexión a PostgreSQL                   | `postgresql://ghibli:...@localhost:5432/ghibli_users`    |
| `SQL_ECHO`          | No          | La API                     | Si es `true`, imprime en consola cada consulta SQL. Por defecto `false` | `true`                       |

- **Dentro de Docker** no hace falta `DATABASE_URL`: Docker Compose la arma con `POSTGRES_*` y el host `db`, y fuerza `SQL_ECHO=false`.
- **Fuera de Docker**, la app lee el `.env` con `python-dotenv`. Si falta `DATABASE_URL`, no arranca.

---

## Migraciones

El esquema de la base se versiona con [Alembic](https://alembic.sqlalchemy.org/), el equivalente a `makemigrations` / `migrate` de Django. Las migraciones viven en `migrations/versions/` y van numeradas (`0001_create_users.py`, `0002_...`).

| Django                        | Alembic                                         |
|-------------------------------|-------------------------------------------------|
| `manage.py makemigrations`    | `uv run alembic revision --autogenerate --rev-id 0002 -m "add email"` |
| `manage.py migrate`           | `uv run alembic upgrade head`                   |
| `manage.py migrate users zero`| `uv run alembic downgrade base`                 |

**Para cambiar el esquema:**

1. Modifica el modelo en `app/modules/users/models.py` (por ejemplo, agrega una columna).
2. Genera la migración con el siguiente número:
   ```bash
   uv run alembic revision --autogenerate --rev-id 0002 -m "add email"
   ```
3. Revisa el archivo generado en `migrations/versions/`. El autogenerate no detecta todo, por ejemplo los renombres de columnas.
4. Aplícala en tu base local:
   ```bash
   uv run alembic upgrade head
   ```
5. Haz commit de la migración junto con el cambio al modelo. En producción se aplica sola cuando el contenedor arranca.

Para ver en qué migración está la base: `uv run alembic current`.

---

## Comandos útiles

```bash
# Instalar o actualizar dependencias
uv sync

# Agregar una dependencia nueva
uv add <paquete>

# Levantar la API en local
uv run uvicorn app.main:app --reload

# Levantar todo con Docker (API + PostgreSQL) / apagarlo
docker compose up -d --build
docker compose down

# Levantar solo PostgreSQL (para desarrollo local)
docker compose up -d db

# Ver los logs
docker compose logs -f api
docker compose logs -f db

# Aplicar migraciones / ver la migración actual
uv run alembic upgrade head
uv run alembic current

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
- **Autenticación y roles:** la API no tiene autenticación; cualquiera que llegue a la URL puede crear o borrar usuarios. Además, `rol` acepta cualquier texto. Está planeado para después de la primera release.
- **Tests:** la carpeta `tests/` todavía no tiene pruebas.

---

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).
