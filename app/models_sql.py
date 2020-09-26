from collections import defaultdict
from datetime import datetime
import os
import json
import random
from time import time

from flask import current_app
from flask_login import UserMixin
from hashlib import md5
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    role = db.relationship('Player', backref='user', lazy='dynamic')

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
        return serializer.dumps({'confirm': self.id})

    def confirm(self, token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.commit()
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def role_in_room(self, room_name):
        room = Room.query.filter_by(name=room_name).first()
        roles = self.role.all()
        for role in roles:
            if role.room_id == room.id:
                return role
        else:
            return None
    
    def is_host(self, room_name):
        role = self.role_in_room(room_name)
        if role is not None:
            return role.is_host
        else:
            return False

    def current_role(self, room_name):
        room_id = Room.query.filter_by(name=room_name).first().id
        return self.role.filter_by(room_id=room_id).first()
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
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
    return User.query.get(int(user_id))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, nullable=False)
    game = db.relationship('Game', backref='room', uselist=False)
    players = db.relationship('Player', backref='room', lazy=True)
    
    def __repr__(self):
        return f"{self.name}: {self.game.template}"
    
    @property
    def round(self):
        return self.game.current_round
    
    @property
    def host(self):
        for p in self.players:
            if p.is_host:
                return p
        else:
            raise ValueError('No host find')
    
    @property
    def sheriff(self):
        for p in self.survivals:
            if p.is_sheriff:
                return p.seat
        else:
            0
        
    @property
    def normal_players(self):
        players = []
        for p in self.players:
            if not p.is_host:
                players.append(p)
        return players
    
    @property
    def available_seats(self):
        seats = set(range(1, 13))
        for p in self.normal_players:
            if p.seat:
                seats -= set([p.seat])
        return list(seats)
    
    @property
    def seated_players(self):
        players = []
        for p in self.players:
            if not p.is_host and p.seat:
                players.append(p)
        return players
    
    @property
    def is_full(self):
        if len(self.seats == 0):
            return True
        else:
            return False
    
    @property
    def template(self):
        return self.game.template
    
    @property
    def survivals(self):
        survivals = []
        for p in self.seated_players:
            if not p.is_dead:
                survivals.append(p)
        return survivals
    
    @property
    def dead(self):
        dead = []
        for p in self.seated_players:
            if p.is_dead:
                dead.append(p)
        return dead
    
    @property
    def description(self):
        desc = {
            "template": self.template,
            "current_stage": self.round,
            "players": []
        }
        for player in self.seated_players:
            desc["players"].append(player.description)
        return desc
    
    @property
    def vote_status(self):
        return self.game.allow_to_vote
    
    @property
    def campaign_status(self):
        return self.game.allow_to_campaign
    
    @property
    def campaign_players(self):
        player_dict = {
            "campaign": [],
            "quit": [],
            "uncampaign": []
        }
        for p in self.survivals:
            if p.in_sheriff_campaign:
                player_dict['campaign'].append(p.seat)
            else:
                if p.sheriff_campaigned:
                    player_dict['quit'].append(p.seat)
                else:
                    player_dict['uncampaign'].append(p.seat)
        return player_dict
    
    @property
    def player_vote_status(self):
        vote_status = []
        for p in self.survivals:
            vote_status.append({
                "seat": p.seat,
                "vote_status": p.capable_for_vote
            })
        return vote_status
    
    @property
    def vote_candidates(self):
        if self.round == "警长竞选":
            candidates = self.campaign_players['campaign']
        else:
            candidates = [p.seat for p in self.survivals if p.is_candidate]
        return candidates
    
    def player_characters(self, user):
        character_list = []
        for p in self.seated_players:
            if user.is_host(self.name):
                row = {'seat': p.seat, 'character': p.character}
            else:
                if p.seat == user.current_role(self.name):
                    row = {
                        'seat': p.seat,
                        'character': user.current_role(self.name).character
                    }
                else:
                    row ={'seat': p.seat, 'character': '-'}
            character_list.append(row)
        return character_list
    
    def allow_votes(self):
        self.game.allow_to_vote = True
        if self.round == "警长竞选":
            # end campaign before vote
            if self.campaign_status:
                self.disable_campaign()
            for p in self.survivals:
                if not p.sheriff_campaigned:
                    p.capable_for_vote = True
                if p.in_sheriff_campaign:
                    p.is_candidate = True
        else:
            for p in self.survivals:
                p.capable_for_vote = True
                p.is_candidate = True
        db.session.commit()
    
    def disable_votes(self):
        self.game.allow_to_vote = False
        for p in self.survivals:
            p.capable_for_vote = False
        db.session.commit()
    
    def set_round(self, round_name):
        self.game.current_round = round_name
        db.session.commit()
    
    def view_vote_results(self, round_name):
        results = {}
        counter = defaultdict(int)
        for p in self.seated_players:
            if not p.is_dead:
                vote = p.votes.filter_by(round=round_name).first()
                if vote and (0 < vote.vote_for <=12):
                    seat = vote.vote_from
                    vote_for = vote.vote_for
                    counter[vote_for] += 1
                else:
                    seat = p.seat
                    vote_for = 0
                results[seat] = {'vote_for': vote_for, 'vote_num': 0}
        for k, v in counter.items():
            results[k]['vote_num'] = v
                                
        data = {'results': [{'vote_from': k, **v} for k, v in results.items()]}
        # get maxinum vote
        max_vote = max([v['vote_num'] for v in data['results']])
        max_vote_seats = list(filter(lambda x: x['vote_num'] == max_vote, data['results']))
        data['max_votes'] = max_vote_seats

        # get vote relationships
        vote_relations = defaultdict(list)
        for v in data['results']:
            vote_relations[v['vote_for']].append(v['vote_from'])
        data['votes'] = vote_relations
        data['round'] = self.round
        return data

    def player_at(self, seat):
        for p in self.seated_players:
            if p.seat == seat:
                return p

    def set_sheriff(self, seat):
        seat = int(seat)
        valid_seats = [p.seat for p in self.survivals]
        valid_seats.append(0) # 0 means destroying the badge
        if seat in valid_seats:
            for p in self.seated_players:
                p.is_sheriff = False
            if seat != 0:
                self.player_at(seat).is_sheriff = True
            db.session.commit()
            return True
        else:
            return False

    def allow_campaign(self):
        self.game.allow_to_campaign = True
        db.session.commit()

    def disable_campaign(self):
        if self.round == "警长竞选":
            self.game.allow_to_campaign = False
            db.session.commit()

    def kill(self, seat, method="死亡"):
        seat = int(seat)
        valid_seats = [p.seat for p in self.survivals]
        if seat in valid_seats:
            self.player_at(seat).death_method = method
            self.player_at(seat).is_dead = True
            db.session.commit()
            return True
        else:
            return False
    
    def revive(self, seat):
        seat = int(seat)
        valid_seats = [p.seat for p in self.dead]
        if seat in valid_seats:
            self.player_at(seat).death_method = "复活"
            self.player_at(seat).is_dead = False
            db.session.commit()
            return True
        else:
            return False

    def assign_characters(self):
        if self.game.character_locked:
            pass
        else:
            data_path = os.path.join(os.path.dirname(__file__), 'data/')
            with open(os.path.join(data_path, 'game_config.json')) as f:
                game_templates = json.load(f)
            char_queue = self.build_character_queue(
                game_templates[self.template])
            for i, p in enumerate(self.seated_players):
                p.character = char_queue[i]
                db.session.commit()

    def lock_characters(self):
        # check if all seated players assigned characters
        for p in self.seated_players:
            if p.character is None:
                return False
            
        self.game.character_locked = True
        db.session.commit()
        return True
            

    def build_character_queue(self, template):
        queue = []
        for key, value in template.items():
            for _ in range(value):
                queue.append(key)
        random.shuffle(queue)
        return queue

    def has_user(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        player = user.current_role(self.name)
        if player in self.players:
            return True
        else:
            return False

    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)    
    is_host = db.Column(db.Boolean)
    character = db.Column(db.String(120))
    seat = db.Column(db.Integer)
    is_dead = db.Column(db.Boolean, default=False)
    death_method = db.Column(db.String(120))
    is_candidate = db.Column(db.Boolean, default=False)
    is_sheriff = db.Column(db.Boolean, default=False)
    in_sheriff_campaign = db.Column(db.Boolean, default=False)
    sheriff_campaigned = db.Column(db.Boolean, default=False)
    capable_for_vote = db.Column(db.Boolean, default=False)
    votes = db.relationship('Vote', backref='player', lazy='dynamic')
    
    @property
    def is_seated(self):
        return (self.seat is not None) and (self.seat != 0)
    
    @property
    def name(self):
        return self.user.username
    
    @property
    def description(self):
        description = {
            "seat": int(self.seat),
            "name": self.name,
            "death": self.death_method if self.is_dead else "存活",
            "is_sheriff": self.is_sheriff,
            "in_campaign": self.in_sheriff_campaign,
            "campaigned": self.sheriff_campaigned
        }
        return description
    
    @property
    def game(self):
        return self.room.game
    
    def sit_at(self, seat):
        if self.is_seated:
            return False
        elif seat not in self.room.available_seats:
            return False
        else:
            self.seat = seat
            db.session.commit()
            return True
    
    def stand_up(self):
        if not self.is_seated:
            raise ValueError(f"You are not seated")
        self.seat = None
        db.session.commit()
    
    def vote_for(self, vote_for):
        try:
            vote_for = int(vote_for)
            # check if vote is valid
            if vote_for <= 0 or vote_for > 12:
                vote_for = 0
            round_name = self.room.round

            # clean previous votes in case of pk vote
            prev_votes = Vote.query.filter_by(game_id=self.game.id,
                            player_id=self.id, round=round_name).all()
            if prev_votes:
                for v in prev_votes:
                    db.session.delete(v)
                db.session.commit()
            vote = Vote(game_id=self.game.id, player_id=self.id,
                            vote_for=vote_for, round=round_name)
            db.session.add(vote)
            self.capable_for_vote = False
            db.session.commit()
            return (True, vote.vote_for)
        except Exception as e:
            # reset vote flag
            self.capable_for_vote = True
            return (False, e)
    
    def campaign(self):
        # Allow in and out when allow to campaign
        if self.room.round == '警长竞选' and self.game.allow_to_campaign:
            self.in_sheriff_campaign = True
            self.sheriff_campaigned = True
            db.session.commit()
            return True
        else:
            return False
    
    def quit_campaign(self):
        if self.room.round == '警长竞选' and self.game.allow_to_campaign:
            self.in_sheriff_campaign = False
            self.sheriff_campaigned = True
            db.session.commit()
            return True
        else:
            return False


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    template = db.Column(db.String(120), index=True, nullable=False)
    current_round = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    character_locked = db.Column(db.Boolean, default=False)
    allow_to_vote = db.Column(db.Boolean, default=False)
    allow_to_campaign = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, index=True, default=datetime.now)
    finish_time = db.Column(db.DateTime, index=True)
    votes = db.relationship('Vote', backref='game', lazy='dynamic')

    def __repr__(self):
        return f"{self.id}: {self.template}"
    
    def end(self):
        self.finish_time = datetime.now()
        self.is_active = False
        self.current_round = -1
    
    @property
    def status(self):
        if self.current_round:
            return self.current_round
        else:
            return "等待上帝指令"
    
    

    

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    vote_for = db.Column(db.Integer)
    round = db.Column(db.String(120))

    def __repr__(self):
        return f'Vote from {self.vote_from} to {self.vote_for} at {self.round}'

    def validate(self):
        if self.vote_for <= 0 or self.vote_for >= 13:
            self.vote_for = 0
    
    @property
    def vote_from(self):
        vote_from = Player.query.filter_by(id=self.player_id).first().seat
        return vote_from
