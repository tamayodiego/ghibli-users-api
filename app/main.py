import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.modules.auth.routers import router as auth
from app.modules.ghibli.routers import router as ghibli
from app.modules.role_requests.routers import router as role_requests
from app.modules.users.routers import router as users

# Las tablas se crean con migraciones (uv run alembic upgrade head), no al arrancar

app = FastAPI(title="ghibli-users-api", version="0.3.0")
app.include_router(auth)
app.include_router(users)
app.include_router(role_requests)
app.include_router(ghibli)


# Errores al consultar Studio Ghibli. Se manejan aquí, en un solo lugar,
# para no repetir try/except en cada uno de los endpoints de /ghibli.

# Ghibli no respondió a tiempo
@app.exception_handler(httpx.TimeoutException)
def ghibli_timeout_handler(request: Request, error: httpx.TimeoutException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "Studio Ghibli no respondió a tiempo"},
    )


# Ghibli respondió con error o no se pudo conectar
@app.exception_handler(httpx.HTTPError)
def ghibli_error_handler(request: Request, error: httpx.HTTPError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Error al consultar Studio Ghibli"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
