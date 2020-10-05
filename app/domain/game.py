from .errors import InvalidGameStatus, InvalidGamePlayer
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
        self._seat_dict = {(k+1): None
            for k in range(self.template.player_number)}

    # Game status related
    @property
    def player_number(self):
        return self.template.player_number
    
    @property
    def _valid_seats(self):
        return list(self._seat_dict.keys())

    def start(self):
        self.lock_characters()
        self.in_game = True
        self.shift = '夜'
        self.round = 1

    def _check_in_game(self):
        if not self.in_game:
            raise InvalidGameStatus("Game is not started")

    @property
    def current_round(self):
        self._check_in_game()
        return f"第{self.round}{self.shift}"

    @property
    def current_stage(self):
        self._check_in_game()
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
        self._check_in_game()
        if shift in ('夜', '天'):
            self.shift = shift
        else:
            raise ValueError(f"{shift} is invalid")

    def set_round(self, round: int):
        self._check_in_game()
        if self.in_game:
            if round <= 0:
                raise ValueError(f'Invalid round {round}')
            else:
                self.round = round
        else:
            raise InvalidGameStatus('Game not started yet')

    def move_to_next_round(self):
        if self.shift == '夜':
            self.set_shift('天')
        else:
            self.set_round(self.round+1)
            self.set_shift('夜')
    
    # player join related
    def _check_player_in_game(self, player: Player):
        if player == self.host:
            raise InvalidGamePlayer(f'{player} has been set as host already')
        elif player in self.audience:
            raise InvalidGamePlayer(f'{player} is audience')
        elif player in self.seated_players:
            raise InvalidGamePlayer(f'{player} is seated')

    def set_host(self, host: Player):
        if self.host is None:
            self._check_player_in_game(host)
            self.host = host
        else:
            raise InvalidGamePlayer('Host has been set already')

    def join_audience(self, audience_player: Player):
        self._check_player_in_game(audience_player)
        self.audience.append(audience_player)
    
    @property
    def available_seats(self):
        return [k for k, v in self._seat_dict.items() if v is None]
    
    @property
    def seated_players(self):
        players = [v for v in self._seat_dict.values() if v]
        return players

    def seat_player(self, player: Player, seat: int):
        if player == self.host:
            raise InvalidGamePlayer(f'{player} has been set as host already')
        if seat in self.available_seats:
            if player in self.seated_players:
                raise InvalidGamePlayer(f'{player} is seated')
            else:
                # TODO: this has side effect, consider SRP
                player.sit_at(seat, self.available_seats)
                self._seat_dict[seat] = player
                if player in self.audience:
                    self.audience.remove(player)
        else:
            raise InvalidGameStatus(f"{seat} is taken")
    
    def player_at_seat(self, seat: int):
        if seat in self._valid_seats:
            return self._seat_dict[seat]
        else:
            raise InvalidGameStatus(f"{seat} is taken")

    # assign characters
    def assign_characters(self):
        if self.character_locked:
            raise InvalidGameStatus("Characters are locked")
        char_queue = self.template.shuffle_characters()
        for seat, player in self._seat_dict.items():
            player.accept_character(char_queue[seat-1])
        self.character_assigned = True

    def lock_characters(self):
        if self.character_assigned:
            self.character_locked = True
        else:
            raise InvalidGameStatus("Characters are not assigned")


    # Sheriff and vote related
    def start_sheriff_campaign(self):
        self._check_in_game()
        if self.round in (1, 2) and self.shift == '天':
            self.in_campaign = True
            self.allow_to_campaign = True
        else:
            msg = f"Cannot start sheriff campaign at {self.current_round}"
            raise InvalidGameStatus(msg)
    
    def end_sheriff_nomination(self):
        self._check_in_game()
        self.allow_to_campaign = False
    
    def end_sheriff_campaign(self):
        self.end_sheriff_nomination()
        self.in_campaign = False

    def start_vote(self, is_pk: bool=False):
        self._check_in_game()
        if self.shift == '天':
            self.in_vote = True
            self.is_pk = is_pk
            # TODO: this has side effect, consider SRP
            for p in self.seated_players:
                p.enable_vote(self.in_campaign, is_pk)
        else:
            msg = f"Cannot start vote at {self.current_round}"
            raise InvalidGameStatus(msg)

    def end_vote(self):
        self._check_in_game()
        self.in_vote = False
        self.is_pk = False

    def set_winner(self, winner_camp: str):
        self.winner = winner_camp
        self.finished = True
