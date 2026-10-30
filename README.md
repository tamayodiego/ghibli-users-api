# ghibli-users-api

API REST para la gestión de usuarios, pensada para controlar con roles el acceso a la API de Studio Ghibli. Está construida con **FastAPI**, **PostgreSQL**, **SQLAlchemy** y **Alembic**, y se despliega con **Docker Compose**.

> **Estado actual:** el CRUD de usuarios está completo y guarda los datos en PostgreSQL. Tiene registro, login con JWT y permisos por rol: solo un `admin` puede crear, editar o borrar usuarios. Cada usuario consume la API de Studio Ghibli según su rol, a través de `/ghibli`.

---

## Índice

- [Cómo ejecutar la aplicación](#cómo-ejecutar-la-aplicación)
- [Autenticación y roles](#autenticación-y-roles)
- [Endpoints](#endpoints)
- [Gateway a Studio Ghibli](#gateway-a-studio-ghibli)
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

Abre `.env` y cambia:

- `POSTGRES_PASSWORD` por una contraseña real.
- `JWT_SECRET_KEY` por una clave aleatoria. Con ella se firman los tokens; puedes generar una con `openssl rand -hex 32`.

Docker Compose lee de ahí estos valores y no arranca si falta alguno.

> ⚠️ PostgreSQL solo toma la contraseña la **primera vez** que crea el volumen de datos. Si después la cambias en el `.env`, la base sigue usando la anterior. Define la contraseña buena antes del primer `up`.

**3. Levantar la base de datos y crear el primer admin**

El admin se crea **antes** de exponer la API, para que nadie pueda registrarse con ese username mientras tanto.

```bash
docker compose build
docker compose up -d db
docker compose run --rm api sh -c "alembic upgrade head && python -m app.create_admin --name 'Totoro' --username totoro --password una-contraseña-segura"
```

`docker compose run` crea un contenedor temporal que aplica las migraciones, crea el admin y se borra al terminar. No publica el puerto `8000`, así que la API todavía no es accesible. Solo se hace una vez. Ver [por qué hace falta](#el-primer-admin).

**4. Levantar la API**

```bash
docker compose up -d api
```

Esto hace lo siguiente:

1. Espera a que el healthcheck de PostgreSQL 17 (`ghibli-users-db`) diga que está listo.
2. Levanta la API (`ghibli-users-api`), que aplica las migraciones pendientes (`alembic upgrade head`) y después arranca uvicorn en el puerto `8000`.

Los dos contenedores tienen `restart: unless-stopped`: si se caen o se reinicia el servidor, vuelven a levantarse solos. Los datos se guardan en el volumen `pgdata`.

**5. Comprobar que funciona**

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

- Revisa que la contraseña de `DATABASE_URL` sea la misma que `POSTGRES_PASSWORD`.
- Cambia `JWT_SECRET_KEY` por una clave aleatoria (`openssl rand -hex 32`).
- Si quieres ver en consola las consultas SQL, deja `SQL_ECHO=true`.

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

**5. Crear el primer admin**

```bash
uv run python -m app.create_admin --name "Totoro" --username totoro --password secreta123
```

**6. Ejecutar la API**

```bash
uv run uvicorn app.main:app --reload
```

`--reload` reinicia el servidor cada vez que guardas un archivo.

> Si ya tienes corriendo el contenedor `api` de la opción A, apágalo con `docker compose stop api`, porque los dos usan el puerto `8000`.

### Documentación interactiva

Con la API corriendo, de cualquiera de las dos formas, FastAPI genera documentación desde donde puedes probar cada endpoint:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

En Swagger, el botón **Authorize** recibe el token. Pega solo el `access_token`, sin la palabra `Bearer`.

---

## Autenticación y roles

### Cómo funciona

1. Te registras con `POST /auth/register` (sin rol) o un admin te crea con `POST /users/`. La contraseña se guarda con hash (argon2), nunca en texto plano.
2. Inicias sesión con `POST /auth/login`, que te devuelve un **JWT** (`access_token`).
3. En los demás requests mandas el token en el header:
   ```
   Authorization: Bearer <access_token>
   ```

El token no se guarda en la base de datos. Lleva dentro el id del usuario (`sub`) y su fecha de expiración (`exp`), y está firmado con `JWT_SECRET_KEY`. Al recibirlo, la API revisa la firma y que no haya expirado. Si alguien modifica el token, la firma deja de coincidir y se rechaza. Por defecto dura 30 minutos (`JWT_EXPIRE_MINUTES`).

### Roles

El `rol` de un usuario solo puede ser uno de estos:

`admin`, `films`, `people`, `locations`, `species`, `vehicles`

Cualquier otro valor responde `422`. La base de datos también lo valida, porque la columna es un enum de PostgreSQL.

Un usuario también puede **no tener rol** (`rol: null`). Es lo que pasa al registrarse: el usuario puede iniciar sesión, pero no tiene acceso a nada hasta que un admin le asigna un rol, ya sea aprobando una [solicitud de rol](#solicitudes-de-rol) o con `PATCH /users/{id}`. El usuario puede solicitar cualquier rol menos `admin`, pero nunca se lo asigna él mismo: solo un admin puede asignarlo, porque el rol decide a qué datos puede entrar. Para quitarle el acceso a alguien, un admin le pone `rol: null`.

### Permisos

| Acción                                      | Sin token | Sin rol | Cualquier otro rol | `admin` |
|---------------------------------------------|-----------|---------|--------------------|---------|
| `/health`, `/auth/register`, `/auth/login`  | ✅        | ✅      | ✅                 | ✅      |
| `/auth/me`                                  | `401`     | ✅      | ✅                 | ✅      |
| Listar y ver usuarios                       | `401`     | `403`   | ✅                 | ✅      |
| Crear, editar y borrar usuarios             | `401`     | `403`   | `403`              | ✅      |
| Crear y ver sus propias solicitudes de rol  | `401`     | ✅      | ✅                 | ✅      |
| Ver, aprobar y negar todas las solicitudes  | `401`     | `403`   | `403`              | ✅      |
| `/ghibli/{recurso}` de **su** rol           | `401`     | `403`   | ✅                 | ✅      |
| `/ghibli/{recurso}` de **otro** rol         | `401`     | `403`   | `403`              | ✅      |

- **`401 Unauthorized`:** no mandaste token, o es inválido o ya expiró.
- **`403 Forbidden`:** el token es válido, pero tu usuario todavía no tiene rol (`"Tu usuario todavía no tiene rol asignado"`) o tu rol no tiene permiso.

`/auth/me` sí acepta usuarios sin rol, para que puedan ver si ya les asignaron uno.

### Solicitudes de rol

Un usuario pide un rol con `POST /role-requests/`, y un admin la aprueba o la niega. Sirve tanto para usuarios sin rol como para cambiar de rol.

1. El usuario crea la solicitud con el rol que quiere (nunca `admin`). Queda en estado `pending` y recibe un **folio**.
2. El admin la revisa por id o por folio, y la aprueba (`approve`) o la niega (`reject`), con un comentario opcional.
3. Al aprobarla, el usuario recibe el rol **en la misma transacción**: o pasan las dos cosas, o ninguna.

Reglas:

- Un usuario solo puede tener **una solicitud `pending`** a la vez (`409`). Lo garantiza un índice único parcial en la base de datos.
- No se puede pedir el rol que ya tienes (`409`).
- Una solicitud ya aprobada o negada no se puede volver a revisar (`409`).
- El **folio** son 6 dígitos aleatorios (por ejemplo `048213`), único, pensado para que una persona lo pueda dictar o buscar. El `id` (UUID) sigue siendo el identificador técnico.

### El primer admin

En `/auth/register` no se puede elegir rol, y crear admins por `POST /users/` necesita el token de otro admin. Por eso el primero se crea desde la terminal, sin pasar por la API:

```bash
uv run python -m app.create_admin --name "Totoro" --username totoro --password secreta123
```

En Docker se corre en un contenedor temporal, antes de levantar la API (ver [Opción A, paso 3](#opción-a-todo-con-docker-producción)), para que nadie se registre con ese username mientras tanto.

> La contraseña queda en el historial de la terminal. Cámbiala después o borra esa línea del historial.

---

## Endpoints

### Resumen

| Método   | Ruta               | Acceso         | Descripción                           | Respuesta exitosa          |
|----------|--------------------|----------------|---------------------------------------|----------------------------|
| `GET`    | `/health`          | Público        | Comprueba que la API está viva        | `200` `{"status": "ok"}`   |
| `POST`   | `/auth/register`   | Público        | Registra un usuario sin rol           | `201` `UserResponse`       |
| `POST`   | `/auth/login`      | Público        | Inicia sesión y devuelve un JWT       | `200` `TokenResponse`      |
| `GET`    | `/auth/me`         | Con token      | Devuelve el usuario dueño del token   | `200` `UserResponse`       |
| `POST`   | `/users/`          | Admin          | Crea un usuario con cualquier rol     | `201` `UserResponse`       |
| `GET`    | `/users/`          | Con token      | Lista usuarios con paginación         | `200` `PaginatedUsers`     |
| `GET`    | `/users/{user_id}` | Con token      | Obtiene un usuario por id             | `200` `UserResponse`       |
| `PUT`    | `/users/{user_id}` | Admin          | Reemplaza nombre y rol del usuario    | `200` `UserResponse`       |
| `PATCH`  | `/users/{user_id}` | Admin          | Actualiza solo los campos enviados    | `200` `UserResponse`       |
| `DELETE` | `/users/{user_id}` | Admin          | Borra un usuario                      | `204` sin cuerpo           |
| `DELETE` | `/users/`          | Admin          | Borra varios usuarios                 | `200` `UserDeleteResponse` |
| `POST`   | `/role-requests/`  | Con token      | Solicita un rol                       | `201` `RoleRequestResponse` |
| `GET`    | `/role-requests/me` | Con token     | Mis solicitudes, de la más nueva a la más vieja | `200` `list[RoleRequestResponse]` |
| `GET`    | `/role-requests/me/last` | Con token | Mi última solicitud                  | `200` `RoleRequestResponse` |
| `GET`    | `/role-requests/`  | Admin          | Lista solicitudes (filtro `?status=`) | `200` `PaginatedRoleRequests` |
| `GET`    | `/role-requests/{request_id}` | Admin | Obtiene una solicitud por id         | `200` `RoleRequestResponse` |
| `GET`    | `/role-requests/folio/{folio}` | Admin | Obtiene una solicitud por folio     | `200` `RoleRequestResponse` |
| `POST`   | `/role-requests/{request_id}/approve` | Admin | Aprueba y asigna el rol      | `200` `RoleRequestResponse` |
| `POST`   | `/role-requests/{request_id}/reject` | Admin | Niega la solicitud            | `200` `RoleRequestResponse` |
| `GET`    | `/ghibli/{recurso}` | Su rol o admin | Listado resumido de un recurso de Ghibli | `200` lista de resúmenes |
| `GET`    | `/ghibli/{recurso}/{id}` | Su rol o admin | Un recurso de Ghibli completo   | `200` detalle            |

- Los ids de usuario son **UUID**, por ejemplo `3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb`.
- Si el body o los parámetros no cumplen con el schema (falta un campo obligatorio, un tipo incorrecto, un rol que no existe, `limit` fuera de rango, etc.), cualquier endpoint responde **`422 Unprocessable Entity`** con el detalle del error.
- Los endpoints con token responden `401` o `403` según la [tabla de permisos](#permisos).
- Los endpoints con `{user_id}` responden `404` si el usuario no existe, y crear un usuario con un `username` que ya existe responde `409`.

---

### `GET /health`

Comprueba que la API está levantada. No consulta la base de datos.

**Respuesta `200`:**
```json
{ "status": "ok" }
```

---

### `POST /auth/register`

Registra un usuario nuevo **sin rol** (`rol: null`). Es público, pero el usuario no tiene acceso a nada hasta que un admin le asigna un rol.

**Body (`RegisterRequest`):**

| Campo      | Tipo     | Obligatorio | Descripción                                |
|------------|----------|-------------|--------------------------------------------|
| `name`     | `string` | Sí          | Nombre del usuario                         |
| `username` | `string` | Sí          | Nombre para iniciar sesión; debe ser único |
| `password` | `string` | Sí          | Contraseña; se guarda solo su hash         |

```json
{
  "name": "Chihiro",
  "username": "chihiro",
  "password": "secreta123"
}
```

**Respuesta `201` (`UserResponse`):**
```json
{
  "name": "Chihiro",
  "rol": null,
  "id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9",
  "username": "chihiro"
}
```

La respuesta nunca incluye la contraseña ni su hash.

**Errores:**
- `422` si se manda `rol` (o cualquier campo que no esté en el body).
- `409` si el `username` ya existe: `"El username ya existe"`.

---

### `POST /auth/login`

Revisa el usuario y la contraseña y devuelve un JWT.

**Body (`LoginRequest`):**

```json
{
  "username": "chihiro",
  "password": "secreta123"
}
```

**Respuesta `200` (`TokenResponse`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errores:** `401` si el usuario no existe o la contraseña es incorrecta: `"Usuario o contraseña incorrectos"`.

---

### `GET /auth/me`

Devuelve el usuario dueño del token.

**Header:** `Authorization: Bearer <access_token>`

**Respuesta `200` (`UserResponse`):**
```json
{
  "name": "Chihiro",
  "rol": "people",
  "id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9",
  "username": "chihiro"
}
```

**Errores:** `401` si no mandas token (`"Not authenticated"`), o si el token es inválido o ya expiró (`"Token inválido o expirado"`).

---

### `POST /users/`

Crea un usuario nuevo con **cualquier** rol, incluido `admin`, o sin rol si no se manda. Solo para admins. El `id` lo genera la base de datos.

**Body (`UserCreate`):** los mismos campos que [`/auth/register`](#post-authregister), más `rol` (opcional, puede ser `admin`).

```json
{
  "name": "Totoro",
  "rol": "admin",
  "username": "totoro",
  "password": "secreta123"
}
```

**Respuesta `201` (`UserResponse`):**
```json
{
  "name": "Totoro",
  "rol": "admin",
  "id": "3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb",
  "username": "totoro"
}
```

**Errores:** `409` si el `username` ya existe: `"El username ya existe"`.

---

### `GET /users/`

Lista los usuarios ordenados por `id`, con paginación. La paginación se hace en SQL (`OFFSET` / `LIMIT`), así que solo se traen de la base los registros de la página pedida.

**Query params:**

| Parámetro | Tipo  | Default | Reglas      | Descripción                           |
|-----------|-------|---------|-------------|---------------------------------------|
| `skip`    | `int` | `0`     | `>= 0`      | Cuántos usuarios saltarse             |
| `limit`   | `int` | `10`    | `1` a `100` | Cuántos usuarios devolver como máximo |

**Ejemplo:** `GET /users/?skip=0&limit=10`

**Respuesta `200` (`PaginatedUsers`):**
```json
{
  "total": 2,
  "skip": 0,
  "limit": 10,
  "data": [
    { "name": "Totoro", "rol": "admin", "id": "3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb", "username": "totoro" },
    { "name": "Chihiro", "rol": "people", "id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9", "username": "chihiro" }
  ]
}
```

`total` es el número total de usuarios en la base, no solo los de esta página. Sirve para calcular cuántas páginas hay.

---

### `GET /users/{user_id}`

Obtiene un usuario por su id.

**Path params:**

| Parámetro | Tipo   | Descripción    |
|-----------|--------|----------------|
| `user_id` | `UUID` | Id del usuario |

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Totoro", "rol": "admin", "id": "3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb", "username": "totoro" }
```

**Errores:** `404` si el usuario no existe: `"Usuario no encontrado"`.

---

### `PUT /users/{user_id}`

Reemplaza el nombre y el rol del usuario. Hay que mandar los dos campos; `"rol": null` le quita el rol. El `username` y la contraseña no se cambian aquí.

**Path params:** `user_id` (`UUID`)

**Body (`UserUpdate`):**

| Campo  | Tipo     | Obligatorio |
|--------|----------|-------------|
| `name` | `string`       | Sí          |
| `rol`  | `Rol` o `null` | Sí          |

```json
{
  "name": "Chihiro",
  "rol": "locations"
}
```

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Chihiro", "rol": "locations", "id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9", "username": "chihiro" }
```

**Errores:** `404` si el usuario no existe: `"Usuario no encontrado"`.

---

### `PATCH /users/{user_id}`

Actualiza **solo los campos que mandes** en el body. Los demás quedan como estaban.

**Path params:** `user_id` (`UUID`)

**Body (`UserPatch`):** todos los campos son opcionales.

| Campo  | Tipo     | Obligatorio |
|--------|----------|-------------|
| `name` | `string` | No          |
| `rol`  | `Rol`    | No          |

```json
{ "rol": "species" }
```

**Respuesta `200` (`UserResponse`):**
```json
{ "name": "Chihiro", "rol": "species", "id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9", "username": "chihiro" }
```

**Errores:** `404` si el usuario no existe: `"Usuario no encontrado"`.

---

### `DELETE /users/{user_id}`

Borra un usuario por su id.

**Path params:** `user_id` (`UUID`)

**Respuesta `204 No Content`:** sin cuerpo.

**Errores:** `404` si el usuario no existe: `"Usuario no encontrado"`.

---

### `DELETE /users/`

Borra varios usuarios a la vez y dice cuáles se borraron y cuáles no existían.

**Body (`UserDelete`):**

| Campo   | Tipo         | Obligatorio | Descripción                  |
|---------|--------------|-------------|------------------------------|
| `users` | `list[UUID]` | Sí          | Ids de los usuarios a borrar |

```json
{
  "users": [
    "3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb",
    "00000000-0000-0000-0000-000000000000"
  ]
}
```

**Respuesta `200` (`UserDeleteResponse`):**
```json
{
  "users_deleted": ["3ab6336d-b7ab-4f3e-bd21-c9ce7b481edb"],
  "users_dont_deleted": ["00000000-0000-0000-0000-000000000000"]
}
```

- `users_deleted`: ids que existían y se borraron.
- `users_dont_deleted`: ids que no existían en la base.

> En Postman, el body de un `DELETE` se manda igual que en un `POST`: pestaña **Body** → **raw** → **JSON**.

---

### `POST /role-requests/`

Crea una solicitud de rol para el usuario del token. Acepta usuarios sin rol.

**Body (`RoleRequestCreate`):**
```json
{ "requested_rol": "films" }
```

**Respuesta `201` (`RoleRequestResponse`):**
```json
{
  "id": "8d2f6c1a-4b3e-4f2a-9c1d-2e3f4a5b6c7d",
  "folio": "048213",
  "user_id": "3925d6e7-05f8-46e0-888b-a8e17734a7a9",
  "requested_rol": "films",
  "status": "pending",
  "review_comment": null,
  "reviewed_by": null,
  "created_at": "2026-10-30T18:00:00Z",
  "reviewed_at": null
}
```

**Errores:**
- `409` si ya tienes una solicitud pendiente: `"Ya tienes una solicitud pendiente"`.
- `409` si pides el rol que ya tienes: `"Ya tienes ese rol"`.
- `422` si pides `admin`: `"No se puede solicitar el rol admin"`.

---

### `GET /role-requests/me` y `GET /role-requests/me/last`

- `/me` devuelve todas tus solicitudes, de la más nueva a la más vieja (`200`, lista vacía si no tienes).
- `/me/last` devuelve solo la más reciente. `404` si no tienes ninguna: `"No tienes solicitudes"`.

---

### `GET /role-requests/`

Solo admin. Lista las solicitudes con paginación, de la más nueva a la más vieja.

| Parámetro | Tipo     | Default | Descripción                                    |
|-----------|----------|---------|------------------------------------------------|
| `status`  | `string` | todos   | `pending`, `approved` o `rejected`             |
| `skip`    | `int`    | `0`     | Cuántas saltar                                 |
| `limit`   | `int`    | `10`    | Cuántas devolver (máximo 100)                  |

**Respuesta `200` (`PaginatedRoleRequests`):** `{"total", "skip", "limit", "data": [RoleRequestResponse]}`.

---

### `GET /role-requests/{request_id}` y `GET /role-requests/folio/{folio}`

Solo admin. Obtienen una solicitud por su UUID o por su folio de 6 dígitos.

- `404` si no existe: `"Solicitud no encontrada"`.
- `422` si el id no es un UUID o el folio no son exactamente 6 dígitos.

---

### `POST /role-requests/{request_id}/approve` y `/reject`

Solo admin. Aprueban o niegan una solicitud pendiente. Al aprobar, el usuario recibe el rol solicitado en la misma transacción.

**Body (`RoleRequestReview`, opcional):**
```json
{ "comment": "Aprobado por el equipo de películas" }
```

**Respuesta `200` (`RoleRequestResponse`):** la solicitud con `status` en `approved` o `rejected`, y con `reviewed_by`, `reviewed_at` y `review_comment` llenos.

**Errores:**
- `404` si la solicitud no existe.
- `409` si ya fue aprobada o negada: `"La solicitud ya fue revisada"`.

---

## Gateway a Studio Ghibli

La API consulta la [API de Studio Ghibli](https://ghibliapi.vercel.app) y regresa sus datos según el rol del usuario. Los roles se llaman igual que los recursos de Ghibli.

### Endpoints

Por cada recurso hay dos endpoints: un **listado resumido** y el **detalle completo**.

| Recurso     | Listado resumido              | Detalle completo                    | Rol que accede        |
|-------------|-------------------------------|-------------------------------------|-----------------------|
| Películas   | `GET /ghibli/films`           | `GET /ghibli/films/{film_id}`       | `films` o `admin`     |
| Personajes  | `GET /ghibli/people`          | `GET /ghibli/people/{person_id}`    | `people` o `admin`    |
| Lugares     | `GET /ghibli/locations`       | `GET /ghibli/locations/{location_id}` | `locations` o `admin` |
| Especies    | `GET /ghibli/species`         | `GET /ghibli/species/{species_id}`  | `species` o `admin`   |
| Vehículos   | `GET /ghibli/vehicles`        | `GET /ghibli/vehicles/{vehicle_id}` | `vehicles` o `admin`  |

- El listado acepta `?limit=N` (de 1 a 250). Sin `limit`, regresa todos.
- El listado regresa resúmenes: `{id, title}` en películas y `{id, name}` en lo demás.

**Ejemplo:** `GET /ghibli/films/2baf70d1-42bb-4437-b551-e5fed5a87abe` (usuario con rol `films`):

```json
{
  "id": "2baf70d1-42bb-4437-b551-e5fed5a87abe",
  "title": "Castle in the Sky",
  "original_title": "天空の城ラピュタ",
  "original_title_romanised": "Tenkū no shiro Rapyuta",
  "image": "https://image.tmdb.org/t/p/w600_and_h900_bestv2/npOnzAbLh6VOIu3naU5QaEcTepo.jpg",
  "movie_banner": "https://image.tmdb.org/t/p/w533_and_h300_bestv2/3cyjYtLWCBE1uvWINHFsFnE8LUK.jpg",
  "description": "The orphan Sheeta inherited a mysterious crystal...",
  "director": "Hayao Miyazaki",
  "producer": "Isao Takahata",
  "release_date": "1986",
  "running_time": "124",
  "rt_score": "95",
  "people": [
    { "id": "fe93adf2-2f3a-4ec4-9f68-5422f1b87c01", "name": "Pazu" }
  ],
  "species": [{ "id": "af3910a6-429f-4c74-9ad5-dfe1c4aa04f2", "name": "Human" }],
  "locations": [],
  "vehicles": [{ "id": "4e09b023-f650-4747-9ab9-eacf14540cfb", "name": "Air Destroyer Goliath" }]
}
```

(`people` recortado; trae todos los personajes de la película).

### Decisiones de diseño

- **Links como resúmenes.** Ghibli enlaza un recurso con otros mediante URLs (por ejemplo, una película trae los links de sus personajes). La API nunca regresa esas URLs: las convierte en resúmenes `{id, name}`, para que un usuario vea qué está relacionado sin acceder a recursos de otro rol. El `id` no da acceso: pedir el detalle de un recurso de otro rol responde `403`.
- **Links genéricos.** Algunos links de Ghibli no tienen id (por ejemplo `.../locations/`, cuando no tiene el dato). Se ignoran.
- **Sin el campo `url`.** El link de Ghibli a sí mismo se quita; basta el `id`.
- **Datos tal cual.** Los números vienen como texto (`"124"`, `"1,000"`) y la edad a veces es una palabra (`"Adult"`). Como la API solo los muestra, se dejan como texto.
- **Pedir solo lo necesario.** Para los resúmenes se usa el parámetro `fields` de Ghibli (por ejemplo, `/people?fields=id,name`), así no se descargan los recursos completos.
- **Caché en memoria, perezosa.** Nada se descarga al arrancar. La primera vez que un request necesita algo, se pide a Ghibli y se guarda en memoria durante `GHIBLI_CACHE_SECONDS` (1 día por defecto). Los datos de Ghibli casi nunca cambian, así que la mayoría de los requests se responden sin consultar a Ghibli. Los `404` no se guardan.
- **Ids validados.** Los ids de `/ghibli/.../{id}` deben tener formato UUID (36 caracteres hexadecimales y guiones). Así nunca se manda a Ghibli texto arbitrario en la URL.

### Errores

| Situación                                  | Respuesta |
|--------------------------------------------|-----------|
| El id no existe en Ghibli                  | `404` `"Recurso no encontrado en Studio Ghibli"` |
| El id no tiene formato UUID                | `422`     |
| Tu rol no es el del recurso (ni admin)     | `403` `"Tu rol no tiene acceso a este recurso"` |
| Ghibli no responde en `GHIBLI_TIMEOUT_SECONDS` | `504` `"Studio Ghibli no respondió a tiempo"` |
| Ghibli responde con error o no se puede conectar | `502` `"Error al consultar Studio Ghibli"` |

Los errores `502` y `504` se manejan en un solo lugar, en `app/main.py`, para no repetir el manejo en cada endpoint.

---

## Modelos de datos

### Tabla `users` (modelo SQLAlchemy `User`)

| Columna         | Tipo                | Restricciones                                       |
|-----------------|---------------------|-----------------------------------------------------|
| `id`            | `uuid`              | Llave primaria; lo genera PostgreSQL con `gen_random_uuid()` |
| `name`          | `character varying` | `NOT NULL`                                          |
| `rol`           | `user_rol` (enum)   | Uno de los [roles](#roles), o `NULL` si no tiene rol |
| `username`      | `character varying` | `NOT NULL`, único                                   |
| `password_hash` | `character varying` | `NOT NULL`; hash argon2 de la contraseña            |

### Tabla `role_requests` (modelo SQLAlchemy `RoleRequest`)

| Columna          | Tipo                          | Restricciones                                                  |
|------------------|-------------------------------|----------------------------------------------------------------|
| `id`             | `uuid`                        | Llave primaria; `gen_random_uuid()`                            |
| `folio`          | `char(6)`                     | `NOT NULL`, único; solo dígitos                                |
| `user_id`        | `uuid`                        | `NOT NULL`; FK → `users.id`, `ON DELETE CASCADE`               |
| `requested_rol`  | `user_rol` (enum)             | `NOT NULL`; nunca `admin`                                      |
| `status`         | `role_request_status` (enum)  | `NOT NULL`, default `pending`; `pending`, `approved`, `rejected` |
| `reviewed_by`    | `uuid`                        | FK → `users.id`, `ON DELETE SET NULL`; el admin que la revisó  |
| `review_comment` | `text`                        | Opcional                                                       |
| `created_at`     | `timestamptz`                 | `NOT NULL`, default `now()`                                    |
| `reviewed_at`    | `timestamptz`                 | Se llena al aprobar o negar                                    |

Índice único parcial `uq_role_requests_one_pending_per_user` sobre `user_id` donde `status = 'pending'`: un usuario no puede tener dos solicitudes pendientes.

### Schemas de Pydantic

Son lo que entra y sale de la API; nunca se expone el modelo de base de datos directamente.

**`app/modules/users/schemas.py`:**

| Schema               | Uso                              | Campos                                                   |
|----------------------|----------------------------------|----------------------------------------------------------|
| `UserBase`           | Base de los demás                | `name: str`, `rol: Rol \| None`                         |
| `UserCreate`         | Body de `POST /users/`           | `name`, `rol`, `username: str`, `password: str`          |
| `UserResponse`       | Respuesta con un usuario         | `id: UUID`, `name`, `rol`, `username`                    |
| `UserUpdate`         | Body de `PUT`                    | `name: str`, `rol: Rol \| None` (los dos obligatorios)  |
| `UserPatch`          | Body de `PATCH`                  | `name: str \| None`, `rol: Rol \| None`                  |
| `PaginatedUsers`     | Respuesta de `GET /users/`       | `total: int`, `skip: int`, `limit: int`, `data: list[UserResponse]` |
| `UserDelete`         | Body de `DELETE /users/`         | `users: list[UUID]`                                      |
| `UserDeleteResponse` | Respuesta de `DELETE /users/`    | `users_deleted: list[UUID]`, `users_dont_deleted: list[UUID]` |

**`app/modules/auth/schemas.py`:**

| Schema            | Uso                                  | Campos                                           |
|-------------------|--------------------------------------|--------------------------------------------------|
| `RegisterRequest` | Body de `POST /auth/register`        | `name`, `username`, `password` (sin `rol`)       |
| `LoginRequest`    | Body de `POST /auth/login`           | `username: str`, `password: str`                 |
| `TokenResponse`   | Respuesta del login                  | `access_token: str`, `token_type: str`           |
| `TokenPayload`    | Datos que van dentro del JWT         | `sub: str` (id del usuario), `exp: int`          |

**`app/modules/role_requests/schemas.py`:**

| Schema                  | Uso                                         | Campos                                                     |
|-------------------------|---------------------------------------------|------------------------------------------------------------|
| `RoleRequestCreate`     | Body de `POST /role-requests/`              | `requested_rol: Rol` (no puede ser `admin`)                |
| `RoleRequestReview`     | Body de `/approve` y `/reject`              | `comment: str \| None` (máximo 500 caracteres)            |
| `RoleRequestResponse`   | Respuesta con una solicitud                 | `id`, `folio`, `user_id`, `requested_rol`, `status`, `review_comment`, `reviewed_by`, `created_at`, `reviewed_at` |
| `PaginatedRoleRequests` | Respuesta de `GET /role-requests/`          | `total`, `skip`, `limit`, `data: list[RoleRequestResponse]` |

---

## Probar con Postman

En `postman/ghibli-users-api.postman_collection.json` hay una colección con todos los endpoints.

1. En Postman, dale a **Import** y arrastra el archivo.
2. [Crea un admin](#el-primer-admin) y pon su usuario y contraseña en las variables `username` y `password` de la colección.
3. Corre **Auth → Login**. Su script guarda el token en la variable `token`.
4. Corre **Users → Crear usuario**. Su script guarda el `id` de la respuesta en la variable `userId`.
5. Los demás requests usan `{{token}}` y `{{userId}}` automáticamente. La carpeta **Users** manda el token como Bearer en todos sus requests.

**Auth → Registrar** crea un usuario sin rol con un `username` distinto en cada corrida, así que puedes correrlo las veces que quieras.

Las variables se editan en la pestaña **Variables**:

| Variable   | Valor por defecto                      | Para qué sirve                          |
|------------|----------------------------------------|-----------------------------------------|
| `baseUrl`  | `http://127.0.0.1:8000`                | URL de la API                           |
| `userId`   | `00000000-0000-0000-0000-000000000000` | Lo llena **Crear usuario**              |
| `token`    | vacío                                  | Lo llena **Login**                      |
| `username` | `admin`                                | Usuario con el que inicia sesión **Login** |
| `password` | `cambia-esta-contraseña`               | Contraseña de ese usuario               |

> El token dura 30 minutos. Si empiezas a recibir `401`, vuelve a correr **Login**.

---

## Ver la base de datos

Con estos datos de conexión puedes usar cualquier cliente de PostgreSQL. Usuario, contraseña y base son los de tu `.env`:

| Campo      | Valor                                      |
|------------|--------------------------------------------|
| Host       | `localhost`                                |
| Puerto     | `5432`                                     |
| Usuario    | `POSTGRES_USER` (por defecto `ghibli`)     |
| Contraseña | `POSTGRES_PASSWORD`                        |
| Base       | `POSTGRES_DB` (por defecto `ghibli_users`) |

Algunas opciones:

- **VS Code:** la extensión *Database Client* (de Weijan Chen).
- **macOS:** [TablePlus](https://tableplus.com/).
- **Terminal**, sin instalar nada:
  ```bash
  docker exec -it ghibli-users-db psql -U ghibli -d ghibli_users -c 'SELECT id, name, rol, username FROM users;'
  ```

---

## Estructura del proyecto

```
ghibli-users-api/
├── app/
│   ├── main.py                  # Crea la app FastAPI y registra los routers
│   ├── database.py              # Engine, SessionLocal, Base y get_db
│   ├── create_admin.py          # Script para crear un admin desde la terminal
│   └── modules/
│       ├── auth/
│       │   ├── routers.py       # Endpoints HTTP de /auth
│       │   ├── dependencies.py  # get_current_user y require_admin (protegen endpoints)
│       │   ├── service.py       # Login y lectura del usuario del token
│       │   ├── security.py      # Hash de contraseñas y firma/lectura de JWT
│       │   └── schemas.py       # Schemas de Pydantic de auth
│       ├── ghibli/
│       │   ├── routers.py       # Endpoints HTTP de /ghibli y permiso por rol
│       │   ├── service.py       # Arma los resúmenes y usa la caché
│       │   ├── client.py        # Cliente HTTP (httpx) hacia Studio Ghibli
│       │   ├── cache.py         # Caché en memoria con expiración
│       │   └── schemas.py       # Versiones resumidas y completas de cada recurso
│       ├── role_requests/
│       │   ├── routers.py       # Endpoints HTTP de /role-requests
│       │   ├── service.py       # Reglas: una pendiente por usuario, aprobar y negar
│       │   ├── repository.py    # Acceso a datos y generación del folio
│       │   ├── models.py        # Tabla role_requests y enum RoleRequestStatus
│       │   └── schemas.py       # Schemas de Pydantic de las solicitudes
│       └── users/
│           ├── routers.py       # Endpoints HTTP de /users
│           ├── service.py       # Lógica de negocio
│           ├── repository.py    # Acceso a datos con SQLAlchemy
│           ├── models.py        # Modelo de base de datos (tabla users) y enum Rol
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

El módulo `auth` no tiene `models.py` porque no guarda nada propio: los usuarios y sus contraseñas viven en la tabla `users`, y el token no se guarda.

### Arquitectura por capas

Cada módulo se divide en tres capas. Cada una solo habla con la de abajo:

```
Request HTTP
    │
    ▼
routers.py     → recibe y valida el request, revisa permisos, llama al service y devuelve la respuesta
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
- **El service** tampoco ve modelos de base de datos: recibe y devuelve schemas. Si algo falla, regresa `None` y el router decide qué error HTTP responder.
- **El repository** es la única capa que toca los modelos y la sesión de SQLAlchemy.

El módulo `auth` no tiene repository propio: usa el `UserRepository`. `/auth/register` usa el mismo `UserService` que `POST /users/`.

### Sesión de base de datos por request

Cada endpoint recibe su propio service mediante `Depends`:

```python
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
```

En cada request, FastAPI llama a `get_db`, que abre una sesión. Con esa sesión crea el `UserService`, se lo pasa al endpoint y, al terminar el request, cierra la sesión.

### Cómo se protegen los endpoints

Los permisos también son dependencias, definidas en `app/modules/auth/dependencies.py`:

- `get_current_user` lee el header `Authorization`, valida el token y devuelve el usuario, o responde `401`.
- `require_admin` usa `get_current_user` y responde `403` si el rol no es `admin`.

En `app/modules/users/routers.py` se aplican así:

```python
# Todos los endpoints de /users piden token
router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

# Este además pide rol admin
@router.post("/", ..., dependencies=[Depends(require_admin)])
```

Si la dependencia lanza el error, el endpoint ni siquiera se ejecuta.

---

## Variables de entorno

Se definen en el archivo `.env`; `.env.example` es la plantilla.

| Variable             | Obligatoria | Usada por                        | Descripción                                          | Ejemplo                                               |
|----------------------|-------------|----------------------------------|------------------------------------------------------|-------------------------------------------------------|
| `POSTGRES_USER`      | Sí          | Docker Compose                   | Usuario de PostgreSQL                                | `ghibli`                                              |
| `POSTGRES_PASSWORD`  | Sí          | Docker Compose                   | Contraseña de PostgreSQL                             | `una-contraseña-segura`                               |
| `POSTGRES_DB`        | Sí          | Docker Compose                   | Nombre de la base de datos                           | `ghibli_users`                                        |
| `DATABASE_URL`       | Solo local  | La API fuera de Docker y Alembic | URL de conexión a PostgreSQL                         | `postgresql://ghibli:...@localhost:5432/ghibli_users` |
| `JWT_SECRET_KEY`     | Sí          | La API                           | Clave para firmar los tokens. Si cambia, todos los tokens existentes dejan de servir | salida de `openssl rand -hex 32` |
| `JWT_EXPIRE_MINUTES` | No          | La API                           | Minutos que dura un token. Por defecto `30`          | `30`                                                  |
| `SQL_ECHO`           | No          | La API                           | Si es `true`, imprime en consola cada consulta SQL. Por defecto `false` | `true`                             |
| `GHIBLI_BASE_URL`    | No          | La API                           | URL de la API de Studio Ghibli. Por defecto `https://ghibliapi.vercel.app` | `https://ghibliapi.vercel.app` |
| `GHIBLI_CACHE_SECONDS` | No        | La API                           | Segundos que dura la caché. Por defecto `86400` (1 día) | `86400`                                     |
| `GHIBLI_TIMEOUT_SECONDS` | No      | La API                           | Segundos máximos de espera por petición a Ghibli. Por defecto `5` | `5`                               |

- **Dentro de Docker** no hace falta `DATABASE_URL`: Docker Compose la arma con `POSTGRES_*` y el host `db`, y fuerza `SQL_ECHO=false`.
- **Fuera de Docker**, la app lee el `.env` con `python-dotenv`. Si falta `DATABASE_URL` o `JWT_SECRET_KEY`, no arranca.
- **Nunca subas el `.env` al repositorio** (ya está en `.gitignore`). En un servidor se crea a mano o las variables las pone la plataforma de despliegue.

---

## Migraciones

El esquema de la base se versiona con [Alembic](https://alembic.sqlalchemy.org/), el equivalente a `makemigrations` / `migrate` de Django. Las migraciones viven en `migrations/versions/` y van numeradas:

| Migración | Qué hace                                                        |
|-----------|-----------------------------------------------------------------|
| `0001`    | Crea la tabla `users`                                           |
| `0002`    | Agrega `username` (único) y `password_hash`                     |
| `0003`    | Cambia el `id` de entero a UUID                                 |
| `0004`    | Convierte `rol` en el enum `user_rol` (borra usuarios con roles que no existen) |
| `0005`    | Permite usuarios sin rol (`rol` acepta `NULL`)                                    |
| `0006`    | Crea la tabla `role_requests` y el enum `role_request_status`                     |

| Django                        | Alembic                                         |
|-------------------------------|-------------------------------------------------|
| `manage.py makemigrations`    | `uv run alembic revision --autogenerate --rev-id 0005 -m "add email"` |
| `manage.py migrate`           | `uv run alembic upgrade head`                   |
| `manage.py migrate users zero`| `uv run alembic downgrade base`                 |

**Para cambiar el esquema:**

1. Modifica el modelo, por ejemplo en `app/modules/users/models.py`.
2. Genera la migración con el siguiente número:
   ```bash
   uv run alembic revision --autogenerate --rev-id 0005 -m "add email"
   ```
3. Revisa el archivo generado en `migrations/versions/`. El autogenerate no detecta todo, por ejemplo los renombres de columnas, y no sabe qué hacer con los datos que ya existen. En esos casos la migración se escribe a mano, como `0002`, `0003` y `0004`.
4. Aplícala en tu base local:
   ```bash
   uv run alembic upgrade head
   ```
5. Comprueba que el modelo y la base coinciden:
   ```bash
   uv run alembic check
   ```
6. Haz commit de la migración junto con el cambio al modelo. En producción se aplica sola cuando el contenedor arranca.

Para ver en qué migración está la base: `uv run alembic current`.

---

## Comandos útiles

```bash
# Instalar o actualizar dependencias
uv sync

# Correr las pruebas (no necesitan la base de datos)
uv run python -m unittest

# Agregar una dependencia nueva
uv add <paquete>

# Levantar la API en local
uv run uvicorn app.main:app --reload

# Crear un admin (en local / en Docker)
uv run python -m app.create_admin --name "Totoro" --username totoro --password secreta123
docker compose run --rm api python -m app.create_admin --name "Totoro" --username totoro --password secreta123

# Generar una clave para JWT_SECRET_KEY
openssl rand -hex 32

# Levantar todo con Docker (API + PostgreSQL) / apagarlo
docker compose up -d --build
docker compose down

# Levantar solo PostgreSQL (para desarrollo local)
docker compose up -d db

# Ver los logs
docker compose logs -f api
docker compose logs -f db

# Aplicar migraciones / ver la migración actual / comprobar que el modelo coincide
uv run alembic upgrade head
uv run alembic current
uv run alembic check

# Borrar la base de datos por completo (¡elimina todos los datos!)
docker compose down -v
```

---

## Limitaciones conocidas

Cosas que todavía no funcionan como deberían:

- **Tokens:** no hay logout ni refresh token; un token sigue sirviendo hasta que expira. Como el usuario se vuelve a leer de la base en cada request, un cambio de rol aplica al momento, y si se borra al usuario su token deja de funcionar.
- **Cambiar contraseña o username:** no hay endpoint para hacerlo.
- **Orden de `GET /users/`:** se ordena por `id`, y como es un UUID el orden no significa nada (no es el orden de creación).
- **Tests:** solo hay pruebas unitarias de lo fundamental (seguridad, permisos, validaciones y el servicio de Ghibli). No hay pruebas de los endpoints contra la base de datos.
- **Caché por proceso:** la caché de Ghibli vive en la memoria de cada proceso. Con varias instancias de la API, cada una tiene la suya. Para compartirla haría falta algo como Redis.

---

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).
