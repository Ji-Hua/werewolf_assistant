from tests.conftest import audience_player, dead_player, seated_player
import pytest

from app.domain.models import Player


def test_player_create_correctly():
    player = Player()
    assert player.seat == 0 and (not player.is_seated)
    assert (not player.is_dead) and player.death_status == '存活'
    assert (not player.is_candidate) and (not player.capable_to_vote)
    assert (not player.is_sheriff)
    assert (not player.in_sheriff_campaign) and (not player.sheriff_campaigned)


def test_player_could_sit():
    player = Player()
    valid_seats = list(range(1, 13))
    player.sit_at(4, valid_seats=valid_seats)
    assert player.seat == 4 and player.is_seated


def test_player_could_not_sit_when_seated(seated_player):
    valid_seats = list(range(1, 13))
    with pytest.raises(ValueError):
        seated_player.sit_at(5, valid_seats=valid_seats)


def test_player_could_not_sit_at_wrong_seat():
    valid_seats = [1, 3, 5]
    player = Player()
    with pytest.raises(ValueError):
        player.sit_at(2, valid_seats=valid_seats)


def test_player_could_stand_up(seated_player):
    seated_player.stand_up()
    assert not seated_player.is_seated
    assert seated_player.seat == 0


def test_player_cannot_stand_up_if_not_seated():
    player = Player()
    with pytest.raises(ValueError):
        player.stand_up()


def test_player_could_be_killed(seated_player):
    death_method = '枪杀'
    seated_player.set_dead(death_method)
    assert seated_player.is_dead 
    assert seated_player.death_status == death_method


def test_player_could_revive(dead_player):
    dead_player.revive()
    assert not dead_player.is_dead 
    assert dead_player.death_status == '存活'


def test_player_cannot_revive_if_alive(seated_player):
    with pytest.raises(ValueError):
        seated_player.revive()


def test_player_set_sheriff_correctly(seated_player):
    seated_player.set_sheriff()
    assert seated_player.is_sheriff


def test_player_could_attend_sheriff_campaign_and_quit(seated_player):
    seated_player.attend_campaign()
    assert seated_player.is_sheriff_candidate
    assert seated_player.in_sheriff_campaign
    assert seated_player.sheriff_campaigned
    assert not seated_player.can_vote_for_sheriff(is_pk=False)
    assert not seated_player.can_vote_for_sheriff(is_pk=True)
    assert seated_player.is_sheriff_candidate

    seated_player.quit_campaign()
    assert not seated_player.is_sheriff_candidate
    assert not seated_player.in_sheriff_campaign
    assert seated_player.sheriff_campaigned
    assert not seated_player.can_vote_for_sheriff(is_pk=False)
    assert seated_player.can_vote_for_sheriff(is_pk=True)
    assert not seated_player.is_sheriff_candidate


def test_player_cannot_quit_campaign_unless_campaigned(seated_player):
    with pytest.raises(ValueError):
        seated_player.quit_campaign()


def test_player_could_vote(seated_player):
    pass


def test_dead_player_will_raise(dead_player):
    with pytest.raises(ValueError):
        dead_player.set_dead('死亡')
    
    with pytest.raises(ValueError):
        dead_player.set_sheriff()
    
    with pytest.raises(ValueError):
        dead_player.attend_campaign()
    
    with pytest.raises(ValueError):
        dead_player.quit_campaign()



def test_audience_player_will_raise(audience_player):
    with pytest.raises(ValueError):
        audience_player.set_dead('死亡')

    with pytest.raises(ValueError):
        audience_player.revive()

    with pytest.raises(ValueError):
        audience_player.set_sheriff()

    with pytest.raises(ValueError):
        audience_player.attend_campaign()
    
    with pytest.raises(ValueError):
        audience_player.quit_campaign()

