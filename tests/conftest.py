import pytest

from app.domain import Game, GameTemplate, Player


@pytest.fixture
def game_template():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "狼人": 2,
        "村民": 1,
        "混血儿": 1
    }
    template = GameTemplate(name=name, characters=characters)
    return template

@pytest.fixture
def seated_game(game_template):
    game = Game(name='1234', template=game_template)
    host = Player('host')
    audience = Player('audience1')
    game.set_host(host)
    game.join_audience(audience)
    for i in range(game.player_number):
        game.seat_player(Player(f"player{i+1}"), i+1)
    return game


@pytest.fixture
def prepared_game(seated_game):
    seated_game.assign_characters()
    return seated_game


@pytest.fixture
def started_game(prepared_game):
    prepared_game.start()
    return prepared_game


@pytest.fixture
def seated_player():
    player = Player('Player1')
    valid_seats = [1, 2, 3, 4, 5, 6]
    player.sit_at(4, valid_seats=valid_seats)
    return player


@pytest.fixture
def audience_player():
    player = Player('Player1')
    return player


@pytest.fixture
def dead_player():
    player = Player('Player1')
    valid_seats = [1, 2, 3, 4, 5, 6]
    player.sit_at(4, valid_seats=valid_seats)
    player.set_dead()
    return player
