from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    rol: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True)          # nombre para hacer login
    password_hash: Mapped[str]                  # nunca la contraseña en texto plano
