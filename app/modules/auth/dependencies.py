from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.service import AuthService
from app.modules.users.models import Rol
from app.modules.users.schemas import UserResponse


# Lee el header "Authorization: Bearer <token>"
bearer = HTTPBearer()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# Usuario dueño del token; 401 si no hay token válido
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), servicio_auth: AuthService = Depends(get_auth_service)) -> UserResponse:
    user = servicio_auth.get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return user

# 403 si el usuario del token todavía no tiene rol
def require_rol(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if user.rol is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tu usuario todavía no tiene rol asignado")
    return user

# 403 si el usuario del token no es admin
def require_admin(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if user.rol != Rol.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un admin puede hacer esto")
    return user
