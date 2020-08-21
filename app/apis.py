import json
from urllib.parse import unquote

from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from flask import url_for, make_response

from app import db
from app.models import User, Vote, Game, Room, Player

class Character(Resource):
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and not user.is_host(room.name):
            player = user.current_role(room.name)
            character = player.character or '等待分发'
            file_name = f"character_logo/{character}.png"
            url = unquote(url_for('static', filename=file_name))
            data = {'character': character,
                    'image_url': url,
                     'locked': room.game.character_locked}
        return data

    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if user.is_host(room.name):
            parser = reqparse.RequestParser()
            # Note: need to use flask_restful.inputs.boolean
            parser.add_argument('assign_characters', type=boolean)
            args = parser.parse_args()
            if args['assign_characters']:
                room.assign_characters()
            else:
                room.lock_characters()
        return {'data': room.description, 'locked': room.game.character_locked}