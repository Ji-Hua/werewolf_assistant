from typing import List

from .vote import Vote


class Player:

    def __init__(self, ref):
        # seat = 0 means audience
        self.ref = ref
        self.seat = 0
        self.is_seated = False

        self.character = None

        # death related
        # death_status could be 存活，死亡（夜间死亡）, 放逐(白天公投), 自爆，枪杀，决斗，殉情
        self.is_dead = False
        self.death_method = None

        # sheriff related
        self.is_sheriff = False
        self.in_sheriff_campaign = False
        self.sheriff_campaigned = False

        # vote related
        self.is_candidate = False
        self.capable_to_vote = False
        self._votes = {}  # dictionary of Vote
    
    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.ref == other.ref
    
    def __repr__(self):
        return f"<Player: {self.ref}>"

    @property
    def death_status(self):
        if self.is_dead:
            return self.death_method
        else:
            return "存活"
    
    def _check_seated_and_alive(self):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead already')
        else:
            raise ValueError('Player is not seated')
        

    def sit_at(self, seat: int, valid_seats: List[int]):
        if self.is_seated:
            raise ValueError("player is seated")
        if seat not in valid_seats:
            raise ValueError(f"invalid seat {seat}")
        self.seat = seat
        self.is_seated = True

    def stand_up(self):
        if self.is_seated:
            self.seat = 0
            self.is_seated = False
        else:
            raise ValueError('Player is not seated')

    def set_dead(self, death_method: str='死亡'):
        self._check_seated_and_alive()
        self.is_dead = True
        self.death_method = death_method

    def revive(self):
        if self.is_seated:
            if not self.is_dead:
                raise ValueError('Player is alive')
            self.is_dead = False
            self.death_method = None
        else:
            raise ValueError('Player is not seated')

    def set_sheriff(self):
        self._check_seated_and_alive()
        self.is_sheriff = True

    @property
    def is_sheriff_candidate(self):
        if self.is_seated:
            if self.is_dead:
                return False
            else:
                return self.in_sheriff_campaign
        else:
            raise ValueError('Player is not seated')

    def can_vote_for_sheriff(self, is_pk: bool = False):
        self._check_seated_and_alive()
        if is_pk:
            return (not self.in_sheriff_campaign)
        else:
            return (not self.sheriff_campaigned) and \
                    (not self.in_sheriff_campaign)

    def attend_campaign(self):
        self._check_seated_and_alive()
        self.sheriff_campaigned = True
        self.in_sheriff_campaign = True

    def quit_campaign(self):
        self._check_seated_and_alive()
        if self.in_sheriff_campaign:
            self.in_sheriff_campaign = False
        else:
            raise ValueError('Player is not in sheriff campaign')

    def vote(self, target: int, stage: str, candidates: List[int]):
        self._check_seated_and_alive()
        if self.capable_to_vote:
            if not target in candidates:
                target = 0  # 0 means abstention
            vote = Vote(vote_from=self.seat, vote_for=target)
            self._votes[stage] = vote
        else:
            raise ValueError('Player is not capable for vote')
    
    def check_vote(self, stage):
        return self._votes.get(stage)

    def enable_vote(self, is_campaign: bool=False, is_pk: bool=False):
        self._check_seated_and_alive()
        if is_campaign:
            if self.can_vote_for_sheriff(is_pk):
                self.capable_to_vote = True
            else:
                self.capable_to_vote = False
        else:
            self.capable_to_vote = True

    def disable_vote(self):
        self._check_seated_and_alive()
        self.capable_to_vote = False
    
    def accept_character(self, character: str):
        if self.is_seated:
            self.character = character
        else:
            raise ValueError('Player not seated')
