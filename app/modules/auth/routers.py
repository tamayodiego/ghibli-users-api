from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.routers import get_user_service
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import UserService


router = APIRouter(prefix="/auth", tags=["auth"])

# Lee el header "Authorization: Bearer <token>"
bearer = HTTPBearer()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# Registro: usa el mismo servicio que POST /users/
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_dto: UserCreate, servicio_usuario: UserService = Depends(get_user_service)):
    return servicio_usuario.create_user(user_dto)

# Inicio de sesión: devuelve un JWT
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(login_dto: LoginRequest, servicio_auth: AuthService = Depends(get_auth_service)):
    token = servicio_auth.login(login_dto)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    return token

# Usuario dueño del token
@router.get("/me", response_model=UserResponse)
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer), servicio_auth: AuthService = Depends(get_auth_service)):
    user = servicio_auth.get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return user
