from pydantic import BaseModel


# Body de POST /auth/login
class LoginRequest(BaseModel):
    username: str
    password: str


# Respuesta del login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Datos que viajan dentro del JWT
class TokenPayload(BaseModel):
    sub: str
    exp: int
