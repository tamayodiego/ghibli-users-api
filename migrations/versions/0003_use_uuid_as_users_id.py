"""use uuid as users id

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-27 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Columna nueva con un UUID para cada usuario existente
    op.execute("ALTER TABLE users ADD COLUMN new_id uuid NOT NULL DEFAULT gen_random_uuid()")

    # Se reemplaza el id entero (y su secuencia) por el UUID
    op.execute("ALTER TABLE users DROP CONSTRAINT users_pkey")
    op.execute("ALTER TABLE users DROP COLUMN id")
    op.execute("ALTER TABLE users RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)")


def downgrade() -> None:
    """Downgrade schema."""
    # Los usuarios reciben ids enteros nuevos (1, 2, 3...); los UUID se pierden
    op.execute("ALTER TABLE users ADD COLUMN old_id serial NOT NULL")

    op.execute("ALTER TABLE users DROP CONSTRAINT users_pkey")
    op.execute("ALTER TABLE users DROP COLUMN id")
    op.execute("ALTER TABLE users RENAME COLUMN old_id TO id")
    op.execute("ALTER SEQUENCE users_old_id_seq RENAME TO users_id_seq")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)")
