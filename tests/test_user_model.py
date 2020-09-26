import unittest

from flask import current_app

from app import create_app, db
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_password_setter(self):
        u = User()
        u.password = 'werewolf'
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User()
        u.password = 'werewolf'
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User()
        u.password = 'werewolf'
        self.assertTrue(u.check_password('werewolf'))
        self.assertFalse(u.check_password('seer'))

    def test_password_salts_are_random(self):
        u = User()
        u.password = 'werewolf'
        u2 = User()
        u2.password = 'werewolf'
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_generate_confirmation_token(self):
        u = User()
        self.assertFalse(u.generate_confirmation_token() is None)

    def test_verify_confirmation_token(self):
        u = User(username='someone', email='someone@example.com')
        token = u.generate_confirmation_token()
        self.assertTrue(u.verify_confirmation_token(token))

    def test_verify_confirmation_token_with_false_token(self):
        u = User(username='someone', email='someone@example.com')
        token = u.generate_confirmation_token()
        u2 = User(username='someone_else', email='someone_else@example.com')
        self.assertFalse(u2.verify_confirmation_token(token))

    def test_generate_reset_password_token(self):
        u = User(username='someone', email='someone@example.com')
        token = u.generate_reset_password_token()
        self.assertFalse(token is None)

    def test_read_reset_password_token(self):
        u = User(username='someone', email='someone@example.com')
        token = u.generate_reset_password_token()
        self.assertEqual(User.read_reset_password_token(token), 'someone@example.com')

    def test_read_reset_password_token_return_none_if_wrong_token(self):
        u = User(username='someone', email='someone@example.com')
        token = u.generate_confirmation_token()
        self.assertTrue(User.read_reset_password_token(token) is None)
