import unittest
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User(password = 'werewolf')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password = 'werewolf')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verifiwerewolfion(self):
        u = User(password = 'werewolf')
        self.assertTrue(u.check_password('werewolf'))
        self.assertFalse(u.check_password('seer'))

    def test_password_salts_are_random(self):
        u = User(password='werewolf')
        u2 = User(password='werewolf')
        self.assertTrue(u.password_hash != u2.password_hash)
