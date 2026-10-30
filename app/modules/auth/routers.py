from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.routers import get_user_service
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService


router = APIRouter(prefix="/auth", tags=["auth"])


# Registro: usa el mismo servicio que POST /users/, pero sin permitir admin
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_dto: RegisterRequest, servicio_usuario: UserService = Depends(get_user_service)):
    user = servicio_usuario.create_user(user_dto)
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El username ya existe")
    return user

# Inicio de sesión: devuelve un JWT
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(login_dto: LoginRequest, servicio_auth: AuthService = Depends(get_auth_service)):
    token = servicio_auth.login(login_dto)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    return token

# Usuario dueño del token
@router.get("/me", response_model=UserResponse)
def me(user: UserResponse = Depends(get_current_user)):
    return user
