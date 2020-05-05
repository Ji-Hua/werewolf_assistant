from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), index=True)
    seat = db.Column(db.Integer)
    votes = db.relationship('Vote', backref='player', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seat = db.Column(db.Integer)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    round = db.Column(db.String(120))
    vote_for = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Vote {self.seat} votes for {self.vote_for} in game {self.game_name} at round {self.round_id}>'


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, nullable=False)
    host = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_round = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, index=True, default=datetime.now)
    finish_time = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return f"{self.name}"
    
    def end(self):
        self.finish_time = datetime.now()
        self.is_active = False
        self.current_round = -1




@login.user_loader
def load_user(id):
    return User.query.get(int(id))
