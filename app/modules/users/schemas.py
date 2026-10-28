from uuid import UUID

from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    rol: str

class UserResponse(UserCreate):
    id: UUID

class UserUpdate(UserCreate):
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
