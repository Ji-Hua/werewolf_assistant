from tests.conftest import game_template
import pytest

from app.domain import Game, InvalidGameStatus


def test_game_has_namenad_template(game_template):
    game = Game(name='1234', template=game_template)
    assert game.name == '1234' and game.template == game_template


def test_game_cannot_start_unless_characters_assigned():
    game = Game(name='1234', template=game_template)
    with pytest.raises(InvalidGameStatus):
        game.start()


def test_game_can_start(prepared_game):
    prepared_game.start()
    assert prepared_game.current_stage == "第1夜 夜间行动"