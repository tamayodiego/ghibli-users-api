"""add username and password to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27 21:30:37.584829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Primero nullable, para no fallar con los usuarios que ya existen
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))

    # Usuarios existentes: username único "user_<id>" y sin contraseña válida (no pueden hacer login)
    op.execute("UPDATE users SET username = 'user_' || id, password_hash = '' WHERE username IS NULL")

    op.alter_column('users', 'username', nullable=False)
    op.alter_column('users', 'password_hash', nullable=False)
    op.create_unique_constraint('uq_users_username', 'users', ['username'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'username')
