from datetime import datetime
import json
import os
import random
from time import time

from flask_login import UserMixin
from hashlib import md5
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.relationship('Player', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
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
    
    def avatar(self, size=28):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


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
        if len(self.available_seats) == 0:
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
    def candidates(self):
        candidates = []
        for p in self.survivals:
            if p.is_candidate:
             candidates.append(p.seat)       
        return candidates

    def enable_votes(self):
        if self.round == "警长竞选":
            for p in self.survivals:
                if not p.sheriff_campaigned:
                    p.capable_for_vote = True
                if p.in_sheriff_campaign:
                    p.is_candidate = True
        else:
            for p in self.survivals:
                p.capable_for_vote = True
                p.is_candidate = True
        self.game.vote_stage = self.round
        self.game.in_vote = True
        db.session.commit()

    def disable_votes(self):
        for p in self.survivals:
            p.capable_for_vote = False
            p.is_candidate = False
        self.game.in_vote = False
        db.session.commit()

    def set_round(self, round_name):
        self.game.current_round = round_name
        db.session.commit()

    def view_vote_results(self, round_name):
        results = []
        for p in self.seated_players:
            if not p.is_dead:
                vote = p.votes.filter_by(round=round_name).first()
                if vote is None:
                    row = {'vote_from': p.seat, 'vote_for': 0}
                else:
                    row = {
                        'vote_from': vote.vote_from,
                        'vote_for': vote.vote_for,
                    }
                results.append(row)
        return results

    def player_at(self, seat):
        for p in self.seated_players:
            if p.seat == seat:
                return p
        else:
            return None

    def set_sheriff(self, seat):
        for p in self.seated_players:
            p.is_sheriff = False
        if seat != 0:
            self.player_at(seat).is_sheriff = True
        db.session.commit()

    def campaign(self, seat):
        self.player_at(seat).in_sheriff_campaign = True
        self.player_at(seat).sheriff_campaigned = True
        db.session.commit()

    def quit_campaign(self, seat):
        self.player_at(seat).in_sheriff_campaign = False
        self.player_at(seat).sheriff_campaigned = True
        db.session.commit()

    def kill(self, seat, method="死亡"):
        self.player_at(seat).death_method = method
        self.player_at(seat).is_dead = True
        db.session.commit()

    def has_user(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        player = user.current_role(self.name)
        if player in self.players:
            return True
        else:
            return False
    
    def build_character_queue(self, template):
        queue = []
        for key, value in template.items():
            for _ in range(value):
                queue.append(key)
        random.shuffle(queue)
        return queue

    def assign_characters(self):
        data_path = os.path.join(os.path.dirname(__file__), 'data/')
        with open(os.path.join(data_path, 'game_config.json')) as f:
            game_templates = json.load(f)
        char_queue = self.build_character_queue(
            game_templates[self.template])
        # if self.is_full:
        for i, p in enumerate(self.seated_players):
            p.character = char_queue[i]
            db.session.commit()
    
    
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
            "avatar": self.user.avatar(),
            "name": self.name,
            "character": (self.character if self.character else '-'),
            "death": (self.death_method if self.is_dead else "存活"),
            "is_sheriff": self.is_sheriff,
            "in_campaign": self.in_sheriff_campaign,
            "campaigned": self.sheriff_campaigned
        }
        return description

    def sit_at(self, seat):
        if self.is_seated:
            raise ValueError(f"You are seated at {self.seat}")
        if seat not in self.room.available_seats:
            raise ValueError(f"Someone is sitting at {seat}")
        self.seat = seat
        db.session.commit()
    
    def stand_up(self):
        if not self.is_seated:
            raise ValueError(f"You are not seated")
        self.seat = None
        db.session.commit()
            



class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    template = db.Column(db.String(120), index=True, nullable=False)
    current_round = db.Column(db.String(120), default='准备阶段')
    vote_stage = db.Column(db.String(120))
    in_vote = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
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

