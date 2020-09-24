from collections import defaultdict
import pdb
import random

from flask import current_app
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

from app.models import Game, User

GAME_ID_LENGTH = 4

def random_with_n_digits(n=GAME_ID_LENGTH):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return str(random.randint(range_start, range_end))


def generate_game_token(user, game):
    serializer = Serializer(current_app.config['SECRET_KEY'])
    raw_token_json = ({'user_id': str(user.id), 'game_id': str(game.id)})
    return serializer.dumps(raw_token_json)


def check_game_token(user, game, token):
    serializer = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token)
    except:
        return False
    if data.get('user_id') != str(user.id):
        return False
    if data.get('game_id') != str(game.id):
        return False
    return True

def check_socketio_message(message):
    room_name = message['room_name']
    user = User.objects(id=message['user_id']).first()
    game = Game.objects(room_name=room_name).first()
    if not check_game_token(user, game, message['token']):
        return False
    else:
        return (user, game)
