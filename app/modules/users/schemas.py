from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modules.users.models import Rol

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Username = Annotated[str, StringConstraints(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]

FORBID_EXTRA = ConfigDict(extra="forbid")


# Campos comunes de un usuario
class UserBase(BaseModel):
    name: str
    rol: Rol | None = None

# Al crear se manda la contraseña en texto plano; se guarda solo su hash
class UserCreate(UserBase):
    model_config = FORBID_EXTRA
    name: Name
    username: Username
    password: Password

# Nunca se regresa la contraseña ni su hash
class UserResponse(UserBase):
    id: UUID
    username: str

class UserUpdate(UserBase):
    model_config = FORBID_EXTRA
    name: Name
    rol: Rol | None             # obligatorio en PUT; null quita el rol

class UserPatch(BaseModel):
    model_config = FORBID_EXTRA
    name: Name | None = None
    rol: Rol | None = None

class PaginatedUsers(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[UserResponse]

class UserDelete(BaseModel):
    model_config = FORBID_EXTRA
    users: list[UUID] = Field(min_length=1, max_length=100)

class UserDeleteResponse(BaseModel):
    users_deleted : list[UUID]
    users_dont_deleted : list[UUID]
