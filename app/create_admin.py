# Crea un usuario admin desde la terminal (register no permite admin)
# Uso: uv run python -m app.create_admin --name "Totoro" --username totoro --password secreta123

import argparse

from app.database import SessionLocal
from app.modules.users.models import Rol
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


def main():
    parser = argparse.ArgumentParser(description="Crea un usuario admin")
    parser.add_argument("--name", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        admin = UserService(db).create_user(
            UserCreate(name=args.name, rol=Rol.admin, username=args.username, password=args.password)
        )
    finally:
        db.close()
    print(f"Admin creado: {admin.username} ({admin.id})")


if __name__ == "__main__":
    main()
