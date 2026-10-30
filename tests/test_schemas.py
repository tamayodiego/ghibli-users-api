import unittest

from pydantic import ValidationError

from app.modules.auth.schemas import RegisterRequest
from app.modules.role_requests.schemas import RoleRequestCreate

VALID_USER = {"name": "Chihiro", "username": "chihiro", "password": "secreta123"}


class RegisterTests(unittest.TestCase):

    def test_register_does_not_accept_a_rol(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(**VALID_USER, rol="admin")

    def test_register_rejects_invalid_fields(self):
        invalid_values = [
            ("username", "chihiro@mail.com"),   # caracteres no permitidos
            ("username", "ch"),                 # muy corto
            ("password", "corta"),              # menos de 8 caracteres
        ]
        for field, value in invalid_values:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError):
                    RegisterRequest(**{**VALID_USER, field: value})


class RoleRequestTests(unittest.TestCase):

    def test_admin_rol_cannot_be_requested(self):
        with self.assertRaises(ValidationError):
            RoleRequestCreate(requested_rol="admin")
