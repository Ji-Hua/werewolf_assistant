from typing import Dict, List, NamedTuple, Optional

from .errors import InvalidGameStatus
from .game_template import GameTemplate
from .player import Player


class Game:

    def __init__(self, name: str, template: GameTemplate):
        self.name = name
        self.template = template

        # game status related
        self.in_game = False
        self.finished = False
        self.shift = None  # shoud be 天or夜
        self.round = None  # should be 1,2,..
        self.winner = None

        # vote/campaign related
        self.in_campaign = False
        self.allow_to_campaign = False
        self.in_vote = False
        self.is_pk = False

        # characters related
        self.character_assigned = False
        self.character_locked = False

        # players
        self.host = None
        self.audience = []
        self.seated_players = {}

    def start(self):
        if self.character_assigned:
            self.character_locked = True
            self.in_game = True
            self.shift = '夜'
            self.round = 1
        else:
            raise InvalidGameStatus("Characters are not assigned")

    @property
    def current_round(self):
        return f"第{self.round}{self.shift}"

    @property
    def current_stage(self):
        if self.shift == '夜':
            return f"{self.current_round} 夜间行动"
        else:
            if self.in_campaign:
                return f"{self.current_round} 警长竞选"
            elif self.in_vote:
                return f"{self.current_round} 投票阶段"
            else:
                return f"{self.current_round} 发言阶段"

    def set_shift(self, shift: str):
        if shift in ('夜', '天'):
            self.shift = shift
        else:
            raise ValueError(f"{shift} is invalid")

    def set_round(self, round: int):
        if self.in_game:
            if round <= 0:
                raise ValueError(f'Invalid round {round}')
            else:
                self.round = round
        else:
            raise InvalidGameStatus('Game not started yet')

    def move_to_the_next_round(self):
        if self.shift == '夜':
            self.set_shift('天')
        else:
            self.round += 1
            self.set_shift('夜')

    def move_to_next_stage(self):
        if self.current_stage == '第一夜':
            self.in_campaign = True
        self.move_to_the_next_round()
    

    # TODO: player join


    # TODO: assign characters
