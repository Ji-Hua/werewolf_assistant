from collections import defaultdict
from datetime import datetime
import os
import json
import random
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
    current_stage = db.StringField()
    day_shift = db.BooleanField(default=False)

    # sheriff campaign
    allow_to_campaign = db.BooleanField(default=False)
    in_campaign = db.BooleanField(default=False)

    # vote related
    allow_to_vote = db.BooleanField(default=False)
    sheriff_vote = db.ListField(db.ReferenceField('Player'))
    sheriff = db.IntField()


    # players related
    # TODO: consider using embeded fileds
    seated_players = db.ListField(db.ReferenceField('Player'))
    audience = db.ListField(db.ReferenceField('User'))

    start_time = db.DateTimeField(default=datetime.now)
    finish_time = db.DateTimeField()

    def __repr__(self):
        return f"{self.room_name}: {self.template.name}"
    
    @property
    def seated_players(self):
        players = []
        for p in self.players:
            if not p.is_host and p.seat:
                players.append(p)
        return players
  
   
    # @property
    # def available_seats(self):
    #     seats = set(range(1, self.template.player_number))
    #     for p in self.seated_players:
    #         if p.seat:
    #             seats -= set([p.seat])
    #     return list(seats)
    

    
    # @property
    # def is_full(self):
    #     if len(self.seats == 0):
    #         return True
    #     else:
    #         return False
    
    # @property
    # def survivals(self):
    #     survivals = []
    #     for p in self.seated_players:
    #         if not p.is_dead:
    #             survivals.append(p)
    #     return survivals
    
    # @property
    # def dead(self):
    #     dead = []
    #     for p in self.seated_players:
    #         if p.is_dead:
    #             dead.append(p)
    #     return dead
    
    # @property
    # def description(self):
    #     desc = {
    #         "template": self.template,
    #         "current_stage": self.round,
    #         "players": []
    #     }
    #     for player in self.seated_players:
    #         desc["players"].append(player.description)
    #     return desc
    
    # @property
    # def vote_status(self):
    #     return self.game.allow_to_vote
    
    # @property
    # def campaign_status(self):
    #     return self.game.allow_to_campaign
    
    # @property
    # def campaign_players(self):
    #     player_dict = {
    #         "campaign": [],
    #         "quit": [],
    #         "uncampaign": []
    #     }
    #     for p in self.survivals:
    #         if p.in_sheriff_campaign:
    #             player_dict['campaign'].append(p.seat)
    #         else:
    #             if p.sheriff_campaigned:
    #                 player_dict['quit'].append(p.seat)
    #             else:
    #                 player_dict['uncampaign'].append(p.seat)
    #     return player_dict
    
    # @property
    # def player_vote_status(self):
    #     vote_status = []
    #     for p in self.survivals:
    #         vote_status.append({
    #             "seat": p.seat,
    #             "vote_status": p.capable_for_vote
    #         })
    #     return vote_status
    
    # @property
    # def vote_candidates(self):
    #     if self.round == "警长竞选":
    #         candidates = self.campaign_players['campaign']
    #     else:
    #         candidates = [p.seat for p in self.survivals if p.is_candidate]
    #     return candidates
    
    # def player_characters(self, user):
    #     character_list = []
    #     for p in self.seated_players:
    #         if user.is_host(self.name):
    #             row = {'seat': p.seat, 'character': p.character}
    #         else:
    #             if p.seat == user.current_role(self.name):
    #                 row = {
    #                     'seat': p.seat,
    #                     'character': user.current_role(self.name).character
    #                 }
    #             else:
    #                 row ={'seat': p.seat, 'character': '-'}
    #         character_list.append(row)
    #     return character_list
    
    # def allow_votes(self):
    #     self.game.allow_to_vote = True
    #     if self.round == "警长竞选":
    #         # end campaign before vote
    #         if self.campaign_status:
    #             self.disable_campaign()
    #         for p in self.survivals:
    #             if not p.sheriff_campaigned:
    #                 p.capable_for_vote = True
    #             if p.in_sheriff_campaign:
    #                 p.is_candidate = True
    #     else:
    #         for p in self.survivals:
    #             p.capable_for_vote = True
    #             p.is_candidate = True
    #     db.session.commit()
    
    # def disable_votes(self):
    #     self.game.allow_to_vote = False
    #     for p in self.survivals:
    #         p.capable_for_vote = False
    #     db.session.commit()
    
    # def set_round(self, round_name):
    #     self.game.current_round = round_name
    #     db.session.commit()
    
    # def view_vote_results(self, round_name):
    #     results = {}
    #     counter = defaultdict(int)
    #     for p in self.seated_players:
    #         if not p.is_dead:
    #             vote = p.votes.filter_by(round=round_name).first()
    #             if vote and (0 < vote.vote_for <=12):
    #                 seat = vote.vote_from
    #                 vote_for = vote.vote_for
    #                 counter[vote_for] += 1
    #             else:
    #                 seat = p.seat
    #                 vote_for = 0
    #             results[seat] = {'vote_for': vote_for, 'vote_num': 0}
    #     for k, v in counter.items():
    #         results[k]['vote_num'] = v
                                
    #     data = {'results': [{'vote_from': k, **v} for k, v in results.items()]}
    #     # get maxinum vote
    #     max_vote = max([v['vote_num'] for v in data['results']])
    #     max_vote_seats = list(filter(lambda x: x['vote_num'] == max_vote, data['results']))
    #     data['max_votes'] = max_vote_seats

    #     # get vote relationships
    #     vote_relations = defaultdict(list)
    #     for v in data['results']:
    #         vote_relations[v['vote_for']].append(v['vote_from'])
    #     data['votes'] = vote_relations
    #     data['round'] = self.round
    #     return data

    # def player_at(self, seat):
    #     for p in self.seated_players:
    #         if p.seat == seat:
    #             return p

    # def set_sheriff(self, seat):
    #     seat = int(seat)
    #     valid_seats = [p.seat for p in self.survivals]
    #     valid_seats.append(0) # 0 means destroying the badge
    #     if seat in valid_seats:
    #         for p in self.seated_players:
    #             p.is_sheriff = False
    #         if seat != 0:
    #             self.player_at(seat).is_sheriff = True
    #         db.session.commit()
    #         return True
    #     else:
    #         return False

    # def allow_campaign(self):
    #     self.game.allow_to_campaign = True
    #     db.session.commit()

    # def disable_campaign(self):
    #     if self.round == "警长竞选":
    #         self.game.allow_to_campaign = False
    #         db.session.commit()

    # def kill(self, seat, method="死亡"):
    #     seat = int(seat)
    #     valid_seats = [p.seat for p in self.survivals]
    #     if seat in valid_seats:
    #         self.player_at(seat).death_method = method
    #         self.player_at(seat).is_dead = True
    #         db.session.commit()
    #         return True
    #     else:
    #         return False
    
    # def revive(self, seat):
    #     seat = int(seat)
    #     valid_seats = [p.seat for p in self.dead]
    #     if seat in valid_seats:
    #         self.player_at(seat).death_method = "复活"
    #         self.player_at(seat).is_dead = False
    #         db.session.commit()
    #         return True
    #     else:
    #         return False

    # def assign_characters(self):
    #     if self.game.character_locked:
    #         pass
    #     else:
    #         data_path = os.path.join(os.path.dirname(__file__), 'data/')
    #         with open(os.path.join(data_path, 'game_config.json')) as f:
    #             game_templates = json.load(f)
    #         char_queue = self.build_character_queue(
    #             game_templates[self.template])
    #         for i, p in enumerate(self.seated_players):
    #             p.character = char_queue[i]
    #             db.session.commit()

    # def lock_characters(self):
    #     # check if all seated players assigned characters
    #     for p in self.seated_players:
    #         if p.character is None:
    #             return False
            
    #     self.game.character_locked = True
    #     db.session.commit()
    #     return True
            

    # def build_character_queue(self, template):
    #     queue = []
    #     for key, value in template.items():
    #         for _ in range(value):
    #             queue.append(key)
    #     random.shuffle(queue)
    #     return queue

    # def has_user(self, user_id):
    #     user = User.query.filter_by(id=user_id).first()
    #     player = user.current_role(self.name)
    #     if player in self.players:
    #         return True
    #     else:
    #         return False


class Vote(db.EmbeddedDocument):
    stage = db.StringField(required=True)
    abstention = db.BooleanField(default=False)
    vote_for = db.IntField()

class Player(db.Document):
    user = db.ReferenceField('User')
    character = db.ReferenceField('Character')
    seat = db.IntField()

    # death related
    # death_method could be 死亡（夜间死亡）, 放逐(白天公投), 自爆，枪杀，决斗，殉情
    is_dead = db.BooleanField(required=True, default=False)
    death_method = db.StringField(default='死亡')

    # sheriff campaign
    is_sheriff = db.BooleanField(default=False)
    in_sheriff_campaign = db.BooleanField(default=False)
    sheriff_campaigned = db.BooleanField(default=False)

    # vote related
    is_candidate = db.BooleanField(default=True)
    capable_to_vote = db.BooleanField(default=True)
    votes = db.ListField(db.EmbeddedDocumentField(Vote))


class GameHistory(db.Document):
    pass