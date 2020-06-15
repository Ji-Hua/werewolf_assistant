from flask_restful import Resource, reqparse
from app.models import User, Vote, Game, Room, Player
from app.tools import assign_character, MAX_PLAYERS



class Table(Resource):
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        results = []
        for seat in range(1, MAX_PLAYERS+1):
            player = room.player_at(seat)
            if player is None:
                desc = {"seat": seat}
            else:
                desc = player.description
                if not user.is_host(room.name) and \
                    player != user.current_role(room.name):
                        desc['character'] = "未知"
            results.append(desc)
        return {'results': results}

class Seat(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and not user.is_host(room.name):
            player = user.current_role(room.name)
            parser = reqparse.RequestParser()
            parser.add_argument('seat', type=int, help='Seat taken by user')
            args = parser.parse_args()
            seat = args['seat']
            print(seat)
            if (player.seat is None) or (player.seat == 0):
                if seat == 0:
                    pass
                else:
                    player.sit_at(seat)
            elif (player.seat is not None) or (player.seat != 0):
                if seat == 0:
                    player.stand_up()
                else:
                    pass
            return {'seat': player.seat}
        else:
            return 404
    
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and not user.is_host(room.name):
            player = user.current_role(room.name)
            if player.seat is None:
                seat = 0
            else:
                seat = player.seat
            return {'seat': seat, 'available': room.available_seats}
        else:
            return 404