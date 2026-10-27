# app/routers/items.py
from fastapi import APIRouter, status, Query
from app.database import get_db
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


router = APIRouter(prefix="/users", tags=["users"])
servicio_usuario = UserService(get_db())


#Creación de usuario
@router.post("/",response_model= UserResponse,status_code=status.HTTP_201_CREATED)
def create_user(user_dto: UserCreate):
    return servicio_usuario.create_user(user_dto)

#Obtención de todos los usuarios
@router.get("/", response_model=PaginatedUsers)
def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return servicio_usuario.get_all(skip,limit)

# Obtención de un usuario específico
@router.get("/{user_id}")
def get_user(user_id: int) -> UserResponse:
    return servicio_usuario.seek_user_by_id(user_id)

#Actualización de un usuario
@router.put("/{user_id}")
def full_user_update(user_id: int, user_dto: UserUpdate) -> UserResponse:
    return servicio_usuario.update(user_id,user_dto)

@router.patch("/{user_id}")
def user_update(user_id: int, user_dto: UserPatch):
    return servicio_usuario.update(user_id,user_dto)


#Borrado de usuario(s)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(user_id: int):
    servicio_usuario.delete(user_id)

@router.delete("/")
def delete_users(list_users_dto: UserDelete) -> UserDeleteResponse:
    return servicio_usuario.delete_many(list_users_dto)
