"""use enum for users rol

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES = "'admin', 'films', 'people', 'locations', 'species', 'vehicles'"


def upgrade() -> None:
    """Upgrade schema."""
    # Los usuarios con un rol fuera de la lista se borran (eran datos de prueba)
    op.execute(f"DELETE FROM users WHERE rol NOT IN ({ROLES})")

    op.execute(f"CREATE TYPE user_rol AS ENUM ({ROLES})")
    op.execute("ALTER TABLE users ALTER COLUMN rol TYPE user_rol USING rol::user_rol")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN rol TYPE varchar USING rol::text")
    op.execute("DROP TYPE user_rol")
