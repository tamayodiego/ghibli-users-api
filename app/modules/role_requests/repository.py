import secrets
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.role_requests.models import RoleRequest, RoleRequestStatus
from app.modules.role_requests.schemas import PaginatedRoleRequests, RoleRequestResponse
from app.modules.users.models import Rol, User

# Nombre del índice que impide tener dos solicitudes pendientes
ONE_PENDING_PER_USER_INDEX = "uq_role_requests_one_pending_per_user"

# Veces que se intenta generar un folio que no exista
MAX_FOLIO_ATTEMPTS = 5


def generate_folio() -> str:
    random_number = secrets.randbelow(1_000_000)
    folio_with_leading_zeros = str(random_number).zfill(6)
    return folio_with_leading_zeros


def get_violated_constraint_name(error: IntegrityError) -> str | None:
    database_error = error.orig
    if database_error is None:
        return None
    if not hasattr(database_error, "diag"):
        return None
    return database_error.diag.constraint_name


class RoleRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    # Convierte el modelo de BD al schema de respuesta
    def _to_schema(self, role_request: RoleRequest) -> RoleRequestResponse:
        return RoleRequestResponse.model_validate(role_request)

    def _to_schema_list(self, role_requests: list[RoleRequest]) -> list[RoleRequestResponse]:
        responses = []
        for role_request in role_requests:
            responses.append(self._to_schema(role_request))
        return responses

    # None si el usuario ya tiene una solicitud pendiente.
    # Si el folio generado ya existe, se intenta con otro.
    def add(self, user_id: UUID, requested_rol: Rol) -> RoleRequestResponse | None:
        for attempt in range(MAX_FOLIO_ATTEMPTS):
            role_request = RoleRequest(
                folio=generate_folio(),
                user_id=user_id,
                requested_rol=requested_rol,
            )
            self.db.add(role_request)

            try:
                self.db.commit()
            except IntegrityError as error:
                self.db.rollback()
                violated_constraint = get_violated_constraint_name(error)
                if violated_constraint == ONE_PENDING_PER_USER_INDEX:
                    return None
                # El folio ya existía: se intenta otra vez con uno nuevo
                continue

            self.db.refresh(role_request)
            return self._to_schema(role_request)

        raise RuntimeError("No se pudo generar un folio único")

    def get_by_id(self, request_id: UUID) -> RoleRequestResponse | None:
        role_request = self.db.get(RoleRequest, request_id)
        if role_request is None:
            return None
        return self._to_schema(role_request)

    def get_by_folio(self, folio: str) -> RoleRequestResponse | None:
        query = select(RoleRequest).where(RoleRequest.folio == folio)
        role_request = self.db.scalar(query)
        if role_request is None:
            return None
        return self._to_schema(role_request)

    # Solicitudes de un usuario, de la más nueva a la más vieja
    def get_by_user(self, user_id: UUID) -> list[RoleRequestResponse]:
        query = (
            select(RoleRequest)
            .where(RoleRequest.user_id == user_id)
            .order_by(RoleRequest.created_at.desc())
        )
        role_requests = self.db.scalars(query).all()
        return self._to_schema_list(list(role_requests))

    def get_last_by_user(self, user_id: UUID) -> RoleRequestResponse | None:
        query = (
            select(RoleRequest)
            .where(RoleRequest.user_id == user_id)
            .order_by(RoleRequest.created_at.desc())
            .limit(1)
        )
        role_request = self.db.scalar(query)
        if role_request is None:
            return None
        return self._to_schema(role_request)

    def get_all(self, status: RoleRequestStatus | None, skip: int, limit: int) -> PaginatedRoleRequests:
        list_query = select(RoleRequest)
        count_query = select(func.count()).select_from(RoleRequest)

        if status is not None:
            list_query = list_query.where(RoleRequest.status == status)
            count_query = count_query.where(RoleRequest.status == status)

        list_query = list_query.order_by(RoleRequest.created_at.desc()).offset(skip).limit(limit)

        role_requests = self.db.scalars(list_query).all()
        total = self.db.scalar(count_query)
        if total is None:
            total = 0

        return PaginatedRoleRequests(
            total=total,
            skip=skip,
            limit=limit,
            data=self._to_schema_list(list(role_requests)),
        )

    # Aprueba o niega una solicitud pendiente, en una sola transacción.
    # Al aprobar, también le asigna el rol al usuario.
    # None si la solicitud ya no está pendiente.
    def review(
        self,
        request_id: UUID,
        new_status: RoleRequestStatus,
        admin_id: UUID,
        comment: str | None,
    ) -> RoleRequestResponse | None:
        # with_for_update bloquea la fila: si dos admins revisan la misma
        # solicitud al mismo tiempo, el segundo espera a que termine el primero
        query = (
            select(RoleRequest)
            .where(RoleRequest.id == request_id)
            .where(RoleRequest.status == RoleRequestStatus.pending)
            .with_for_update()
        )
        role_request = self.db.scalar(query)
        if role_request is None:
            self.db.rollback()
            return None

        role_request.status = new_status
        role_request.reviewed_by = admin_id
        role_request.review_comment = comment
        role_request.reviewed_at = func.now()

        if new_status == RoleRequestStatus.approved:
            user = self.db.get(User, role_request.user_id)
            if user is not None:
                user.rol = role_request.requested_rol

        self.db.commit()
        self.db.refresh(role_request)
        return self._to_schema(role_request)
