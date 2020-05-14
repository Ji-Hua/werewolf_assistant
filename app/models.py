from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.relationship('Player', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_host(self):
        return self.role.first().is_host == True
    

    def current_role(self, room_name):
        return self.role.filter_by(room_id=room_name).first()


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
    def host(self):
        for p in self.players:
            if p.is_host:
                return p
        else:
            raise ValueError('No host find')
        
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
            seats -= set(p.seat)
        return seats
    
    @property
    def is_full(self):
        if len(self.normal_players == 12):
            return True
        else:
            return False
    
    @property
    def template(self):
        return self.game.template
    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)    
    is_host = db.Column(db.Boolean)
    character = db.Column(db.String(120))
    seat = db.Column(db.Integer)
    is_dead = db.Column(db.Boolean, default=False)
    capable_for_vote = db.Column(db.Boolean, default=False)
    votes = db.relationship('Vote', backref='player', lazy='dynamic')
    
    
    @property
    def is_seated(self):
        return self.seat is not None



class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    template = db.Column(db.String(120), index=True, nullable=False)
    current_round = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, index=True, default=datetime.now)
    finish_time = db.Column(db.DateTime, index=True)
    votes = db.relationship('Vote', backref='game', lazy='dynamic')

    def __repr__(self):
        return f"{self.name}: {self.template}"
    
    def end(self):
        self.finish_time = datetime.now()
        self.is_active = False
        self.current_round = -1
    

    

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    vote_for = db.Column(db.Integer)
    round = db.Column(db.String(120))

    def __repr__(self):
        return f'Player at seat {self.seat} votes for {self.vote_for} in game {self.game_id} at round {self.round}'

    def validate(self):
        if self.vote_for <= 0 or self.vote_for >= 13:
            self.vote_for = 0

