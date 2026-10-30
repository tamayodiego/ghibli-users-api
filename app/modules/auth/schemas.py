from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import Name, Password, Username


# Body de POST /auth/register: sin rol, lo asigna un admin después
class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    username: Username
    password: Password


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
