from fastapi import FastAPI
from app.modules.auth.routers import router as auth
from app.modules.users.routers import router as users

# Las tablas se crean con migraciones (uv run alembic upgrade head), no al arrancar

app = FastAPI(title="ghibli-users-api", version="0.1.0")
app.include_router(auth)
app.include_router(users)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}



