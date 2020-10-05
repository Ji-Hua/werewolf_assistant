import random
from typing import Dict, List, NamedTuple, Optional


class Skill(NamedTuple):
    name: str
    intro: str

    def __repr__(self):
        return f"{self.name}: {self.intro}"


class Character(NamedTuple):
    name: str
    camp: List[str]
    skills: Optional[List[Skill]] = []
    lines: Optional[str] = ''
    background: Optional[str] = ''
    note: Optional[str] = ''


class Vote(NamedTuple):
    vote_from: int
    vote_for: Optional[int] = 0


class GameTemplate:

    def __init__(self, name: str, 
            characters: Dict[str, int], player_number: int=12):
        self.name = name
        self.characters = characters
        self.player_number = player_number

        if sum(self.characters.values()) != self.player_number:
            raise ValueError(f'Number of characters does not match player_number')

    def __repr__(self):
        text = f"{self.name} ({self.player_number} 人): \n"
        for key, value in self.characters.items():
            text += f"{key}x{value}\n"
        return text

    def __eq__(self, other):
        for name, num in self.characters.items():
            if name not in other.characters:
                return False
            if num != other.characters[name]:
                return False
        return True

    @property
    def description(self):
        return self.__repr__()
    
    def shuffle_characters(self):
        queue = []
        for key, value in self.characters.items():
            for _ in range(value):
                queue.append(key)
        random.shuffle(queue)
        return queue


class Player:

    def __init__(self):
        # seat = 0 means audience
        self.seat = 0
        self.is_seated = False

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

    @property
    def death_status(self):
        if self.is_dead:
            return self.death_method
        else:
            return "存活"

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
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead already')
            self.is_dead = True
            self.death_method = death_method
        else:
            raise ValueError('Player is not seated')

    def revive(self):
        if self.is_seated:
            if not self.is_dead:
                raise ValueError('Player is alive')
            self.is_dead = False
            self.death_method = None
        else:
            raise ValueError('Player is not seated')

    def set_sheriff(self):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            self.is_sheriff = True
        else:
            raise ValueError('Player is not seated')

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
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            if is_pk:
                return (not self.in_sheriff_campaign)
            else:
                return (not self.sheriff_campaigned) and \
                    (not self.in_sheriff_campaign)
        else:
            raise ValueError('Player is not seated')

    def attend_campaign(self):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            self.sheriff_campaigned = True
            self.in_sheriff_campaign = True
        else:
            raise ValueError('Player is not seated')

    def quit_campaign(self):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            if self.in_sheriff_campaign:
                self.in_sheriff_campaign = False
            else:
                raise ValueError('Player is not in sheriff campaign')
        else:
            raise ValueError('Player is not seated')

    def vote(self, target: int, stage: str, candidates: List[int]):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            if self.capable_to_vote:
                if not target in candidates:
                    target = 0  # 0 means abstention
                vote = Vote(vote_from=self.seat, vote_for=target)
                self._votes[stage] = vote
            else:
                raise ValueError('Player is not capable for vote')
        else:
            raise ValueError('Player is not seated')

    def enable_vote(self, is_campaign: bool=False, is_pk: bool=False):
        if self.is_seated:
            if self.is_dead:
                raise ValueError('Player is dead')
            if is_campaign:
                if self.can_vote_for_sheriff(is_pk):
                    self.capable_to_vote = True
                else:
                    self.capable_to_vote = False
        else:
            raise ValueError('Player is not seated')

    

class Game:

    def __init__(self, name:str, template: GameTemplate):
        self.name = name
        self.template = template
