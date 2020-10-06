from app.domain import player
import pytest

from app.domain import Player, Vote


def test_player_create_correctly():
    player = Player('Player1')
    assert player.seat == 0 and (not player.is_seated)
    assert (not player.is_dead) and player.death_status == '存活'
    assert (not player.is_candidate) and (not player.capable_to_vote)
    assert (not player.is_sheriff)
    assert (not player.in_sheriff_campaign) and (not player.sheriff_campaigned)


def test_player_could_sit():
    player = Player('Player1')
    valid_seats = list(range(1, 13))
    player.sit_at(4, valid_seats=valid_seats)
    assert player.seat == 4 and player.is_seated


def test_player_could_not_sit_when_seated(seated_player):
    valid_seats = list(range(1, 13))
    with pytest.raises(ValueError):
        seated_player.sit_at(5, valid_seats=valid_seats)


def test_player_could_not_sit_at_wrong_seat():
    valid_seats = [1, 3, 5]
    player = Player('Player1')
    with pytest.raises(ValueError):
        player.sit_at(2, valid_seats=valid_seats)


def test_player_could_stand_up(seated_player):
    seated_player.stand_up()
    assert not seated_player.is_seated
    assert seated_player.seat == 0


def test_player_cannot_stand_up_if_not_seated():
    player = Player('Player1')
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


def test_player_cannot_vote_unless_enabled(seated_player):
    with pytest.raises(ValueError):
        stage = "警长竞选"
        candidates = [1, 2, 3, 4]
        seated_player.vote(target=1, stage=stage, candidates=candidates)


def test_player_vote_correctly_at_regular_stage(seated_player):
    stage = "警长竞选"
    candidates = [1, 2, 3, 4]
    seated_player.enable_vote()
    seated_player.vote(target=1, stage=stage, candidates=candidates)
    vote = Vote(vote_from=seated_player.seat, vote_for=1)
    assert seated_player.check_vote(stage) == vote
    seated_player.disable_vote()
    with pytest.raises(ValueError):
        seated_player.vote(target=1, stage=stage, candidates=candidates)


def test_player_cannot_vote_for_sheriff_in_campaign(seated_player):
    seated_player.attend_campaign()
    seated_player.enable_vote(is_campaign=True)
    assert not seated_player.capable_to_vote
    seated_player.enable_vote(is_campaign=True, is_pk=True)
    assert not seated_player.capable_to_vote
    

def test_player_could_abstain_in_vote(seated_player):
    stage = "警长竞选"
    candidates = [1, 2, 3, 4]
    target = 0
    seated_player.enable_vote()
    seated_player.vote(target, stage, candidates)
    vote = Vote(vote_from=seated_player.seat, vote_for=target)
    assert seated_player.check_vote(stage) == vote


def test_player_vote_treated_as_abstention_if_invalid(seated_player):
    stage = "警长竞选"
    candidates = [1, 2, 3, 4]
    seated_player.enable_vote()
    seated_player.vote(5, stage, candidates)
    vote = Vote(vote_from=seated_player.seat, vote_for=0)
    assert seated_player.check_vote(stage) == vote


def test_player_cannot_vote_for_sheriff_in_campaign(seated_player):
    seated_player.attend_campaign()
    seated_player.quit_campaign()
    seated_player.enable_vote(is_campaign=True)
    assert not seated_player.capable_to_vote
    seated_player.enable_vote(is_campaign=False)
    assert seated_player.capable_to_vote


def test_player_could_accept_character_correctly(seated_player):
    seated_player.accept_character('预言家')
    assert seated_player.character == '预言家'


def test_dead_player_will_raise(dead_player):
    with pytest.raises(ValueError):
        dead_player.set_dead('死亡')
    
    with pytest.raises(ValueError):
        dead_player.set_sheriff()
    
    with pytest.raises(ValueError):
        dead_player.attend_campaign()
    
    with pytest.raises(ValueError):
        dead_player.quit_campaign()
    
    with pytest.raises(ValueError):
        dead_player.enable_vote()
    
    with pytest.raises(ValueError):
        stage = "警长竞选"
        candidates = [1, 2, 3, 4]
        dead_player.vote(target=1, stage=stage, candidates=candidates)



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
    
    with pytest.raises(ValueError):
        audience_player.enable_vote()
    
    with pytest.raises(ValueError):
        audience_player.accept_character('预言家')
    
    with pytest.raises(ValueError):
        stage = "警长竞选"
        candidates = [1, 2, 3, 4]
        audience_player.vote(target=1, stage=stage, candidates=candidates)
