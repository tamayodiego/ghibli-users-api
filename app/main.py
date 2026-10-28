from fastapi import FastAPI
from app.modules.users.routers import router as users
from app.database import Base, engine
from app.modules.users import models  

Base.metadata.create_all(bind=engine)


app = FastAPI(title="ghibli-users-api", version="0.1.0")
app.include_router(users)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}



