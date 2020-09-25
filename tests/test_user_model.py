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

    def test_confirm_works_correctly(self):
        u = User()
        token = u.generate_confirmation_token()
        u.confirm(token)
        self.assertTrue(u.confirmed)
