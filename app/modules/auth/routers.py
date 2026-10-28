from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# Inicio de sesión: devuelve un JWT
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(login_dto: LoginRequest, servicio_auth: AuthService = Depends(get_auth_service)):
    pass

# Usuario dueño del token
@router.get("/me", response_model=UserResponse)
def me(servicio_auth: AuthService = Depends(get_auth_service)):
    pass
