from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.role_requests.models import RoleRequestStatus
from app.modules.role_requests.repository import RoleRequestRepository
from app.modules.role_requests.schemas import (
    PaginatedRoleRequests,
    RoleRequestCreate,
    RoleRequestResponse,
    RoleRequestReview,
)
from app.modules.users.schemas import UserResponse


class RoleRequestService:

    def __init__(self, db: Session):
        self.repo = RoleRequestRepository(db)

    # True si el usuario ya tiene el rol que está pidiendo
    def already_has_rol(self, user: UserResponse, dto: RoleRequestCreate) -> bool:
        return user.rol == dto.requested_rol

    # None si el usuario ya tiene una solicitud pendiente
    def create(self, user: UserResponse, dto: RoleRequestCreate) -> RoleRequestResponse | None:
        return self.repo.add(user.id, dto.requested_rol)

    def get_my_requests(self, user: UserResponse) -> list[RoleRequestResponse]:
        return self.repo.get_by_user(user.id)

    # None si el usuario no tiene solicitudes
    def get_my_last_request(self, user: UserResponse) -> RoleRequestResponse | None:
        return self.repo.get_last_by_user(user.id)

    def get_all(self, status_filter: RoleRequestStatus | None, skip: int, limit: int) -> PaginatedRoleRequests:
        return self.repo.get_all(status_filter, skip, limit)

    # None si no existe
    def get_by_id(self, request_id: UUID) -> RoleRequestResponse | None:
        return self.repo.get_by_id(request_id)

    # None si no existe
    def get_by_folio(self, folio: str) -> RoleRequestResponse | None:
        return self.repo.get_by_folio(folio)

    # None si la solicitud ya no está pendiente
    def approve(self, request_id: UUID, admin: UserResponse, dto: RoleRequestReview) -> RoleRequestResponse | None:
        return self.repo.review(request_id, RoleRequestStatus.approved, admin.id, dto.comment)

    # None si la solicitud ya no está pendiente
    def reject(self, request_id: UUID, admin: UserResponse, dto: RoleRequestReview) -> RoleRequestResponse | None:
        return self.repo.review(request_id, RoleRequestStatus.rejected, admin.id, dto.comment)
