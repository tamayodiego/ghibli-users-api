import enum
import uuid
from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, Enum, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.modules.users.models import Rol


class RoleRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RoleRequest(Base):
    __tablename__ = "role_requests"
    __table_args__ = (
        CheckConstraint("folio ~ '^[0-9]{6}$'", name="ck_role_requests_folio_digits"),
        CheckConstraint("requested_rol <> 'admin'", name="ck_role_requests_not_admin"),
        # Un usuario solo puede tener una solicitud pendiente a la vez
        Index(
            "uq_role_requests_one_pending_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    folio: Mapped[str] = mapped_column(CHAR(6), unique=True)          # 6 dígitos aleatorios, para humanos
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    requested_rol: Mapped[Rol] = mapped_column(Enum(Rol, name="user_rol", create_type=False))
    status: Mapped[RoleRequestStatus] = mapped_column(
        Enum(RoleRequestStatus, name="role_request_status"), server_default=RoleRequestStatus.pending.value
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    review_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
