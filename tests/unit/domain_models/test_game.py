from tests.conftest import prepared_game, started_game
import pytest

from app.domain.errors import InvalidGamePlayer, InvalidGameStatus
from app.domain import Game, Player


def test_game_can_initialize_correctly(game_template):
    game = Game(name='1234', template=game_template)
    assert game.name == '1234' and game.template == game_template
    assert len(game._seat_dict) == game_template.player_number

    host = Player('host')
    game.set_host(host)
    assert game.host == host

    audience = Player('audience1')
    game.join_audience(audience)
    assert audience in game.audience

    for i in range(game.player_number):
        game.seat_player(Player(f"player{i+1}"), i+1)
    player = Player(f"player3")
    assert player == game.player_at_seat(3)
    assert len(game.available_seats) == 0

    with pytest.raises(InvalidGameStatus):
        game.seat_player(audience, 1)


def test_game_could_seat_players(game_template):
    game = Game(name='1234', template=game_template)

    player = Player('audience1')
    game.join_audience(player)
    game.seat_player(player, game.available_seats[0])
    assert player not in game.audience
    assert player in game.seated_players


def test_game_will_raise_if_invalid_player(game_template):
    game = Game(name='1234', template=game_template)
    player = Player('audience1')
    game.join_audience(player)
    assert player in game.audience

    with pytest.raises(InvalidGamePlayer):
        game.join_audience(player)
    
    with pytest.raises(InvalidGamePlayer):
        game.set_host(player)


def test_game_could_assign_characters(seated_game):
    seated_game.assign_characters()
    for p in seated_game.seated_players:
        assert p.character is not None

def test_game_cannot_lock_unless_characters_assigned(seated_game):
    with pytest.raises(InvalidGameStatus):
        seated_game.lock_characters()


def test_game_cannot_assign_characters_when_locked(seated_game):
    seated_game.assign_characters()
    seated_game.lock_characters()
    with pytest.raises(InvalidGameStatus):
        seated_game.assign_characters()


def test_Game_could_set_round_correctly(prepared_game):
    with pytest.raises(InvalidGameStatus):
        prepared_game.set_round(1)

    prepared_game.start()
    assert prepared_game.round == 1

    with pytest.raises(ValueError):
        prepared_game.set_round(0)


def test_game_can_start_and_set_stage_correctly(prepared_game):
    prepared_game.start()
    assert prepared_game.in_game
    assert prepared_game.current_round == "第1夜"
    prepared_game.move_to_next_round()
    assert prepared_game.current_round == "第1天"


def test_game_can_start_and_end_sheriff_campaign(started_game):
    started_game.move_to_next_round()
    started_game.start_sheriff_campaign()
    assert started_game.in_campaign and started_game.allow_to_campaign
    assert started_game.current_stage == "第1天 警长竞选"
    started_game.end_sheriff_nomination()
    assert started_game.in_campaign and (not started_game.allow_to_campaign)
    started_game.end_sheriff_campaign()
    assert (not started_game.in_campaign) and (not started_game.allow_to_campaign)
    assert started_game.current_stage == "第1天 发言阶段"


def test_game_could_allow_vote(started_game):
    started_game.move_to_next_round()
    started_game.start_vote(True)
    assert started_game.in_vote
    assert started_game.is_pk
    assert started_game.current_stage == "第1天 投票阶段"
    started_game.end_vote()
    assert not started_game.in_vote

def test_game_set_winner(started_game):
    started_game.set_winner("好人")
    assert started_game.finished
    assert started_game.winner == "好人"
