import unittest
from unittest.mock import patch

import jwt

from app.modules.auth import security


class PasswordTests(unittest.TestCase):

    def test_hash_verifies_only_the_right_password(self):
        hashed = security.hash_password("secreta123")

        self.assertNotEqual(hashed, "secreta123")
        self.assertTrue(security.verify_password("secreta123", hashed))
        self.assertFalse(security.verify_password("otra-cosa", hashed))


class TokenTests(unittest.TestCase):

    def test_token_keeps_the_user_id(self):
        token = security.create_access_token("user-123")

        self.assertEqual(security.decode_access_token(token).sub, "user-123")

    def test_tampered_token_is_rejected(self):
        token = security.create_access_token("user-123")
        header, payload, signature = token.split(".")
        tampered = f"{header}.{payload}.{signature[::-1]}"

        with self.assertRaises(jwt.InvalidTokenError):
            security.decode_access_token(tampered)

    def test_expired_token_is_rejected(self):
        with patch.object(security, "EXPIRE_MINUTES", -1):
            token = security.create_access_token("user-123")

        with self.assertRaises(jwt.ExpiredSignatureError):
            security.decode_access_token(token)
