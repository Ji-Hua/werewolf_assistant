from datetime import datetime
from time import time

from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

class User(UserMixin, db.Document):
    # TODO: Add game related documents
    email = db.EmailField(required=True, unique=True, null=False)
    username = db.StringField(required=True, unique=True, null=False)
    password_hash = db.StringField(required=True)
    confirmed = db.BooleanField(default=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def generate_confirmation_token(self, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'confirm': str(self.id)})

    def confirm(self, token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except:
            return False
        if data.get('confirm') != str(self.id):
            return False

        self.confirmed = True
        self.save()
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': str(self.id), 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


# NOTE: Flask-login needs a callback function to load user
# with a unique id
@login.user_loader
def load_user(user_id):
    return User.objects(id=str(user_id)).get()


class Skill(db.EmbeddedDocument):
    name = db.StringField(required=True, null=False)
    introduction = db.StringField(required=True, null=False)


class Character(db.Document):
    name = db.StringField(required=True, unique=True)
    name_en = db.StringField(null=True)
    camp = db.ListField(db.StringField(), required=True)
    skills = db.ListField(db.EmbeddedDocumentField(Skill))
    image = db.FileField()
    note = db.StringField()
    backgroud_story = db.StringField()

    def __repr__(self):
        return f"<Character {self.name}>"

class GameTemplate(db.Document):
    name = db.StringField(required=True, unique=True)
    player_number = db.IntField(required=True, default=12)
    characters = db.DictField(required=True)

    @property
    def description(self):
        text = f"{self.name} ({self.player_number} 人): \n"
        for key, value in self.characters.items():
            text += f"{key}x{value}\n"
        return text


class Vote(db.EmbeddedDocument):
    vote_from = db.IntField(required=True)
    vote_for = db.IntField()
    abstention = db.BooleanField(default=False)


class VoteResult(db.EmbeddedDocument):
    raw_votes = db.ListField(db.EmbeddedDocumentField(Vote))
    max_votes = db.ListField()
    vote_counts = db.DictField()
    votes_from = db.MapField(db.ListField())
    round = db.StringField()


class Game(db.Document):
    room_name = db.StringField(required=True, unique=True, null=False)
    template = db.ReferenceField('GameTemplate', null=False, required=True)
    host = db.ReferenceField('User')

    # is_active means if this game is valid or aborted
    is_active = db.BooleanField(default=True)

    # characters related fields
    character_assigned = db.BooleanField(default=False)
    character_locked = db.BooleanField(default=False)

    # in game means this game is being played
    in_game = db.BooleanField(default=False)

    # current_stage indicates the stage of the game
    current_stage = db.StringField(default="准备阶段")
    day_shift = db.BooleanField(default=False)

    # sheriff campaign
    allow_to_campaign = db.BooleanField(default=False)
    allow_to_quit_campaign = db.BooleanField(default=False)
    in_campaign = db.BooleanField(default=False)
    sheriff = db.IntField()

    # vote related
    allow_to_vote = db.BooleanField(default=False)
    sheriff_vote = db.ListField()
    vote_results = db.MapField(db.EmbeddedDocumentField(VoteResult))
    
    # players related
    # TODO: consider using embeded fileds
    seated_players = db.ListField(db.ReferenceField('Player'))
    audience = db.ListField(db.ReferenceField('Player'))

    start_time = db.DateTimeField(default=datetime.now)
    finish_time = db.DateTimeField()

    def __repr__(self):
        return f"<Game {self.room_name}: {self.template.name}>"
    
    @property
    def description(self):
        desc = {
            "template": self.template.description,
            "current_stage": self.current_stage,
            "players": []
        }
        for player in self.seated_players:
            desc["players"].append(player.description)
        return desc

    @property
    def all_players(self):
        return [*self.audience, *self.seated_players]
    
    @property
    def valid_seats(self):
        return set(range(1, self.template.player_number + 1))
    
    @property
    def available_seats(self):
        seats = set(range(1, 13))
        for p in self.seated_players:
            if p.seat:
                seats -= set([p.seat])
        return list(seats)

    @property
    def vote_status(self):
        return self.allow_to_vote
    
    @vote_status.setter
    def vote_status(self, status: bool):
        self.allow_to_vote = status
        self.save()
    
    #TODO: consider to cache this
    @property
    def survivals(self):
        survivals = []
        for p in self.seated_players:
            if not p.is_dead:
                survivals.append(p)
        return survivals
    
    @property
    def player_vote_status(self):
        vote_status = []
        for p in self.survivals:
            vote_status.append({
                "seat": p.seat,
                "vote_status": p.capable_to_vote
            })
        return vote_status
    
    @property
    def vote_candidates(self):
        if self.in_campaign:
            candidates = self.campaign_players['campaign']
        else:
            candidates = [p.seat for p in self.survivals if p.is_candidate]
        return candidates

    @property
    def campaign_players(self):
        # campaign = currently in campaign
        # quit = once attended campagin but quited
        # uncampaign = never attend
        player_dict = {"campaign": [], "quit": [], "uncampaign": []}
        for p in self.survivals:
            player_dict[p.sheriff_campaign_status].append(p.seat)
        return player_dict

    def has_host(self, user_id):
        if str(user_id) == str(self.host.id):
            return True
        else:
            return False

    def has_seated_player(self, user_id):
        seated_player_ids = [str(p.user.id) for p in self.seated_players]
        if str(user_id) in seated_player_ids:
            return True
        else:
            return False

    def has_audience(self, user_id):
        audience_ids = [str(p.user.id) for p in self.audience]
        if str(user_id) in audience_ids:
            return True
        else:
            return False

    def has_player(self, user_id):
        return self.has_audience(user_id) or self.has_seated_player(user_id)

    def has_user(self, user_id):
        return self.has_host(user_id) or self.has_player(user_id)

    def current_player_of(self, user_id):
        player_ids = [str(p.user.id) for p in self.all_players]
        if str(user_id) in player_ids:
            # the if statement has guranteed that this player exits
            player = Player.objects(user=user_id).first()
            return player
        else:
            return None

    def player_characters(self, user_id):
        character_list = []
        for p in self.seated_players:
            if self.has_host(user_id):
                row = {'seat': p.seat, 'character': p.character}
            else:
                player = self.current_player_of(user_id)
                if p.seat == player.seat:
                    row = {
                        'seat': p.seat,
                        'character': player.character.name
                    }
                else:
                    row ={'seat': p.seat, 'character': '-'}
            character_list.append(row)
        return character_list
    
    # Vote related methods
    def check_is_valid_seat(self, seat):
        seat = int(seat)
        if 0 < seat <= self.template.player_number:
            survivals_seats = [p.seat for p in self.survivals]
            if seat in survivals_seats:
                return True
        return False
    
    def allow_votes(self):
        self.allow_to_vote = True
        #FIXME: need to use setters
        if self.in_campaign:
            # end campaign before vote
            if self.campaign_status:
                self.disable_campaign()
            for p in self.survivals:
                if not p.sheriff_campaigned:
                    p.capable_to_vote = True
                if p.in_sheriff_campaign:
                    p.is_candidate = True
        else:
            for p in self.survivals:
                p.capable_to_vote = True
                p.is_candidate = True
        
        self.vote_results[self.round_name] = VoteResult(round=self.round_name)
        self.save()
    
    def disable_votes(self):
        self.allow_to_vote = False
        # FIXME: need to use setters
        for p in self.survivals:
            p.capable_to_vote = False
        self.save()

    # TODO: should use self.round_name
    def add_vote(self, vote, round_name):
        # vote should be in the format of 
        # {'vote_from': 1, 'vote_for': 2}
        # vote for 0 means abstention
        vote_result = self.vote_results.get(round_name)
        if vote_result is None:
            raise Exception(f"{round_name} doesn't exist")
        if self.check_is_valid_seat(vote['vote_from']):
            seat = vote['vote_from']
            if self.check_is_valid_seat(vote['vote_for']):
                target = vote['vote_for']
                vote_result.votes_from[target].append(seat)
                # FIXME: sheriff vote is list
                if seat == self.sheriff and self.sheriff_vote == target:
                    vote_result.vote_counts[target] += 1.5
                else:
                    vote_result.vote_counts[target] += 1
                max_count = max(vote_result.vote_counts.values())
                vote_result.max_votes = [(k, v) for k, v in vote_result.vote_counts.items() if v==max_count]
            else:
                target = 0
            vote = Vote(vote_from=vote['vote_from'], vote_for=target, abstention=(target==0))
            
            vote_result.raw_votes.append(vote)
        self.save()

    def view_vote_results(self, round_name):
        vote_result = self.vote_results.get(round_name)
        if vote_result is None:
            raise Exception(f"{round_name} doesn't exist")
        data = {
            'max_votes': vote_result.max_votes,
            'round': round_name,
            'results': vote_result.raw_votes,
            'votes': vote_result.votes_from
        }
        return data

    def set_round(self, round_name):
        self.current_stage = round_name
        if round_name == '警长竞选':
            self.in_campaign = True
        self.save()
    
    def seat_player(self, player):
        self.audience.remove(player)
        # TODO: should make seated_players a dictionary
        self.seated_players.append(player)
        self.save()


class Player(db.Document):
    user = db.ReferenceField('User')
    game = db.ReferenceField('Game')
    character = db.ReferenceField('Character')
    seat_at = db.IntField()

    # death related
    # death_method could be 死亡（夜间死亡）, 放逐(白天公投), 自爆，枪杀，决斗，殉情
    is_dead = db.BooleanField(required=True, default=False)
    death_method = db.StringField()

    # sheriff campaign
    is_sheriff = db.BooleanField(default=False)
    in_sheriff_campaign = db.BooleanField(default=False)
    sheriff_campaigned = db.BooleanField(default=False)

    # vote related
    is_candidate = db.BooleanField(default=True)
    capable_to_vote = db.BooleanField(default=True)

    @property
    def seat(self):
        return self.seat_at or 0

    @seat.setter
    def seat(self, seat):
        if int(seat) not in self.game.valid_seats:
            raise Exception(f"invalid seat {seat}")
        self.seat_at = seat
        self.save()

    @property
    def is_seated(self):
        return (self.seat in self.game.valid_seats)
    
    @property
    def death_status(self):
        if self.is_dead:
            return self.death_method
        else:
            return "存活"
    
    @property
    def sheriff_campaign_status(self):
        if self.in_sheriff_campaign:
            return 'campaign'
        else:
            if self.sheriff_campaigned:
                return 'quit'
            else:
                return 'uncampaign'
    
    @property
    def description(self):
        description = {
            "seat": int(self.seat),
            "name": self.user.username,
            "death": self.death_status,
            "is_sheriff": self.is_sheriff,
            "in_campaign": self.in_sheriff_campaign,
            "campaigned": self.sheriff_campaigned
        }
        return description
    
    def sit_at(self, seat):
        if self.is_seated:
            return False
        elif seat not in self.game.available_seats:
            return False
        else:
            self.seat = seat
            self.save()
            self.game.seat_player(self)
            return True



class GameHistory(db.Document):
    # TODO: add this later
    pass