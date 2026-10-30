import unittest
import uuid

from fastapi import HTTPException

from app.modules.auth.dependencies import require_admin, require_rol
from app.modules.ghibli.routers import require_access_to
from app.modules.users.models import Rol
from app.modules.users.schemas import UserResponse


def make_user(rol: Rol | None) -> UserResponse:
    return UserResponse(id=uuid.uuid4(), name="Totoro", username="totoro", rol=rol)


class PermissionTests(unittest.TestCase):

    def test_user_without_rol_is_blocked(self):
        with self.assertRaises(HTTPException) as error:
            require_rol(make_user(None))

        self.assertEqual(error.exception.status_code, 403)

    def test_only_admin_passes_require_admin(self):
        admin = make_user(Rol.admin)

        self.assertIs(require_admin(admin), admin)
        with self.assertRaises(HTTPException) as error:
            require_admin(make_user(Rol.films))
        self.assertEqual(error.exception.status_code, 403)

    def test_ghibli_resource_allows_its_rol_and_admin_only(self):
        check_films = require_access_to(Rol.films)

        check_films(make_user(Rol.films))
        check_films(make_user(Rol.admin))
        with self.assertRaises(HTTPException) as error:
            check_films(make_user(Rol.people))
        self.assertEqual(error.exception.status_code, 403)
