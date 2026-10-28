# app/routers/items.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
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


# Todos piden token; crear, editar y borrar además piden rol admin
router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)



#Creación de usuario
@router.post("/",response_model= UserResponse,status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user(user_dto: UserCreate, servicio_usuario: UserService = Depends(get_user_service)):
    return servicio_usuario.create_user(user_dto)

#Obtención de todos los usuarios
@router.get("/", response_model=PaginatedUsers)
def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), servicio_usuario: UserService = Depends(get_user_service)):
    return servicio_usuario.get_all(skip,limit)

# Obtención de un usuario específico
@router.get("/{user_id}")
def get_user(user_id: UUID, servicio_usuario: UserService = Depends(get_user_service)) -> UserResponse:
    return servicio_usuario.seek_user_by_id(user_id)

#Actualización de un usuario
@router.put("/{user_id}", dependencies=[Depends(require_admin)])
def full_user_update(user_id: UUID, user_dto: UserUpdate, servicio_usuario: UserService = Depends(get_user_service)) -> UserResponse:
    return servicio_usuario.update(user_id,user_dto)

@router.patch("/{user_id}", dependencies=[Depends(require_admin)])
def user_update(user_id: UUID, user_dto: UserPatch, servicio_usuario: UserService = Depends(get_user_service)):
    return servicio_usuario.update(user_id,user_dto)


#Borrado de usuario(s)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_user_by_id(user_id: UUID, servicio_usuario: UserService = Depends(get_user_service)):
    servicio_usuario.delete(user_id)

@router.delete("/", dependencies=[Depends(require_admin)])
def delete_users(list_users_dto: UserDelete, servicio_usuario: UserService = Depends(get_user_service)) -> UserDeleteResponse:
    return servicio_usuario.delete_many(list_users_dto)
