# app/routers/items.py
from fastapi import APIRouter, status, Query
from app.modules.users.models import (
    PaginatedUsers,
    UserCreate,
    UserDelete,
    UserPatch,
    UserResponse,
    UserUpdate,
)


router = APIRouter(prefix="/users", tags=["users"])


#Creación de usuario
@router.post("/",response_model= UserResponse,status_code=status.HTTP_201_CREATED)
def create_user(user_dto: UserCreate):
    return UserResponse(id=1, **user_dto.model_dump())

#Obtención de todos los usuarios
@router.get("/", response_model=PaginatedUsers)
def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return PaginatedUsers(total=0, skip=skip, limit=limit, data=[])

# Obtención de un usuario específico
@router.get("/{user_id}")
def get_user(user_id: int):
    return [f"get id_user {user_id}"]

#Actualización de un usuario
@router.put("/{user_id}")
def full_user_update(user_id: int, user_dto: UserUpdate):
    return [f"User put {user_id}"]

@router.patch("/{user_id}")
def user_update(user_id: int, uset_dto: UserPatch):
    return [f"user patch {user_id}"]


#Borrado de usuario(s)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(user_id: int):
    return [f"delte con id {user_id}"]

@router.delete("/")
def delete_users(list_users_dto: UserDelete):
    return [f"delete {list_users_dto.users}"]
