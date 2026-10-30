"""allow users without rol

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Los usuarios registrados no tienen rol hasta que un admin se los asigna
    op.alter_column('users', 'rol', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Falla si hay usuarios sin rol: asígnales uno antes de bajar de versión
    op.alter_column('users', 'rol', nullable=False)
