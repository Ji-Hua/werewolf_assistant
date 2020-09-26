import unittest
from jinja2.environment import Template

import pytest

from app import create_app
from app.models import Player, Game, GameTemplate


class PlayerModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        template = GameTemplate(name='预女猎白', characters={
            "预言家": 1,
            "女巫": 1,
            "猎人": 1,
            "白痴": 1,
            "狼人": 4,
            "村民": 4
        }).save()
        self.game = Game(template=template, room_name='1234').save()

    def tearDown(self):
        GameTemplate.objects(id=self.game.template.id).first().delete()
        self.game.delete()
        Player.objects().delete()
        self.app_context.pop()

    def test_sit_at_right_seat(self):
        p = Player(game=self.game)
        seat = 1
        self.assertTrue(p._sit_at(seat))
    
    def test_sit_at_wrong_seat(self):
        p = Player(game=self.game)
        seat = 13
        self.assertFalse(p._sit_at(seat))
