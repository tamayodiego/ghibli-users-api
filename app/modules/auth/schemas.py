from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.users.models import Rol
from app.modules.users.schemas import UserCreate


# Body de POST /auth/register: cualquier rol menos admin
class RegisterRequest(UserCreate):

    @field_validator("rol")
    @classmethod
    def rol_no_admin(cls, rol: Rol) -> Rol:
        if rol == Rol.admin:
            raise ValueError("No puedes registrarte como admin")
        return rol


# Body de POST /auth/login
class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(max_length=50)
    password: str = Field(max_length=128)


# Respuesta del login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Datos que viajan dentro del JWT
class TokenPayload(BaseModel):
    sub: str
    exp: int
