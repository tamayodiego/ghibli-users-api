from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.role_requests.models import RoleRequestStatus
from app.modules.users.models import Rol

FORBID_EXTRA = ConfigDict(extra="forbid")


# Body de POST /role-requests/
class RoleRequestCreate(BaseModel):
    model_config = FORBID_EXTRA
    requested_rol: Rol

    @field_validator("requested_rol")
    @classmethod
    def rol_no_admin(cls, rol: Rol) -> Rol:
        if rol == Rol.admin:
            raise ValueError("No se puede solicitar el rol admin")
        return rol


# Body de /approve y /reject
class RoleRequestReview(BaseModel):
    model_config = FORBID_EXTRA
    comment: str | None = Field(default=None, max_length=500)


class RoleRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    folio: str
    user_id: UUID
    requested_rol: Rol
    status: RoleRequestStatus
    review_comment: str | None
    reviewed_by: UUID | None
    created_at: datetime
    reviewed_at: datetime | None


class PaginatedRoleRequests(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[RoleRequestResponse]
