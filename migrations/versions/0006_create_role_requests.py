"""create role requests

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-30 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES = ('admin', 'films', 'people', 'locations', 'species', 'vehicles')
STATUSES = ('pending', 'approved', 'rejected')


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE role_request_status AS ENUM ('pending', 'approved', 'rejected')")

    op.create_table(
        'role_requests',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('folio', sa.CHAR(6), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        # user_rol ya existe (0004): se reutiliza sin volver a crearlo
        sa.Column('requested_rol', postgresql.ENUM(*ROLES, name='user_rol', create_type=False), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM(*STATUSES, name='role_request_status', create_type=False),
            server_default='pending',
            nullable=False,
        ),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('folio'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint("folio ~ '^[0-9]{6}$'", name='ck_role_requests_folio_digits'),
        sa.CheckConstraint("requested_rol <> 'admin'", name='ck_role_requests_not_admin'),
    )
    op.create_index('ix_role_requests_user_id', 'role_requests', ['user_id'])
    op.create_index(
        'uq_role_requests_one_pending_per_user',
        'role_requests',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('role_requests')
    op.execute("DROP TYPE role_request_status")
