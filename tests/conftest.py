import pytest

from app.domain.models import GameTemplate, Player


@pytest.fixture
def game_template():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": 1
    }
    return GameTemplate(name=name, characters=characters)


@pytest.fixture
def seated_player():
    player = Player()
    valid_seats = list(range(1, 13))
    player.sit_at(4, valid_seats=valid_seats)
    return player


@pytest.fixture
def audience_player():
    player = Player()
    return player


@pytest.fixture
def dead_player():
    player = Player()
    valid_seats = list(range(1, 13))
    player.sit_at(4, valid_seats=valid_seats)
    player.set_dead()
    return player
