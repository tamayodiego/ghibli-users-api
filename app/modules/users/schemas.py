from uuid import UUID

from pydantic import BaseModel

# Campos comunes de un usuario
class UserBase(BaseModel):
    name: str
    rol: str

# Al crear se manda la contraseña en texto plano; se guarda solo su hash
class UserCreate(UserBase):
    username: str
    password: str

# Nunca se regresa la contraseña ni su hash
class UserResponse(UserBase):
    id: UUID
    username: str

class UserUpdate(UserBase):
    pass

class UserPatch(BaseModel):
    name: str | None = None
    rol: str | None = None

class PaginatedUsers(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[UserResponse]

class UserDelete(BaseModel):
    users: list[UUID]

class UserDeleteResponse(BaseModel):
    users_deleted : list[UUID]
    users_dont_deleted : list[UUID]
