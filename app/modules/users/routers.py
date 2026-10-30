# app/routers/items.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.auth.dependencies import require_admin, require_rol
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    PaginatedUsers,
    UserCreate,
    UserDelete,
    UserPatch,
    UserResponse,
    UserUpdate,
    UserDeleteResponse
)


USER_NOT_FOUND = "Usuario no encontrado"
USERNAME_TAKEN = "El username ya existe"

# Todos piden token de un usuario con rol; crear, editar y borrar además piden rol admin
router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_rol)])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)



#Creación de usuario
@router.post("/",response_model= UserResponse,status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user(user_dto: UserCreate, servicio_usuario: UserService = Depends(get_user_service)):
    user = servicio_usuario.create_user(user_dto)
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USERNAME_TAKEN)
    return user

#Obtención de todos los usuarios
@router.get("/", response_model=PaginatedUsers)
def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), servicio_usuario: UserService = Depends(get_user_service)):
    return servicio_usuario.get_all(skip,limit)

# Obtención de un usuario específico
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, servicio_usuario: UserService = Depends(get_user_service)):
    user = servicio_usuario.seek_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
    return user

#Actualización de un usuario
@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def full_user_update(user_id: UUID, user_dto: UserUpdate, servicio_usuario: UserService = Depends(get_user_service)):
    user = servicio_usuario.update(user_id, user_dto)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
    return user

@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def user_update(user_id: UUID, user_dto: UserPatch, servicio_usuario: UserService = Depends(get_user_service)):
    user = servicio_usuario.update(user_id, user_dto)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
    return user


#Borrado de usuario(s)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_user_by_id(user_id: UUID, servicio_usuario: UserService = Depends(get_user_service)):
    if not servicio_usuario.delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

@router.delete("/", dependencies=[Depends(require_admin)])
def delete_users(list_users_dto: UserDelete, servicio_usuario: UserService = Depends(get_user_service)) -> UserDeleteResponse:
    return servicio_usuario.delete_many(list_users_dto)
