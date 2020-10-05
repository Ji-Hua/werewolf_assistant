from tests.conftest import game_template
import pytest

from app.domain.models import Game


def test_game_has_namenad_template(game_template):
    game = Game(name='1234', template=game_template)
    assert game.name == '1234' and game.template == game_template
