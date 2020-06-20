import json

from flask_restful import Resource, reqparse
from flask import url_for, make_response

from app import db
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


class Character(Resource):
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and not user.is_host(room.name):
            player = user.current_role(room.name)
            character = player.character
            if character:
                data = {'character': character}
            else:
                data = {'character': '等待分发'}
        return data
    
    
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if user.is_host(room.name):
            parser = reqparse.RequestParser()
            parser.add_argument('assign_characters', type=bool)
            args = parser.parse_args()
            if args['assign_characters']:
                room.assign_characters()
        return {'data': room.description}


class Round(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if user.is_host(room.name):
            parser = reqparse.RequestParser()
            parser.add_argument('round_name', type=str,
                                help='Current round of this game')
            parser.add_argument('allow_vote', type=int)
            args = parser.parse_args()
            round_name = args['round_name']
            room.set_round(round_name)

            # Note: different stages of the game
            if round_name == "准备阶段":
                pass # Allow new player sit down or stand up
            elif round_name == "分发身份":
                pass
            else:
                if args['allow_vote'] == 1:
                    room.enable_votes()
                else:
                    room.disable_votes()
            return {'round_name': room.round}
    
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id):
            return {
                'round_name': room.round,
                'vote': user.current_role(room.name).capable_for_vote
            }

class Votes(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and not user.is_host(room.name):
            parser = reqparse.RequestParser()
            parser.add_argument('vote_for', type=int)
            parser.add_argument('round_name', type=str)
            args = parser.parse_args()
            player = user.current_role(room.name)
            if player.capable_for_vote:
                game = Room.query.filter_by(name=room.name).first().game
                prev_votes = Vote.query.filter_by(
                    game_id=game.id, player_id=player.id, round=args['round_name']).all()
                if prev_votes:
                    for v in prev_votes:
                        db.session.delete(v)
                    db.session.commit()
                vote = Vote(game_id=game.id, player_id=player.id,
                            vote_for=args['vote_for'], round=args['round_name'])
                db.session.add(vote)
                db.session.commit()
                player.capable_for_vote = False
                db.session.commit()
                return {"vote": args['vote_for']}
            else:
                return {"vote": -1}
        else:
                return {"vote": -1}
    
    def get(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id):
            vote_stage = room.game.vote_stage
            results = room.view_vote_results(vote_stage)
            results = sorted(results, key=lambda x: x['vote_from'])
            counter = {}
            for row in results:
                value = row['vote_for']
                if value > 0 and value < 12:
                    count = counter.get(value, 0.0)
                    if room.player_at(row['vote_from']).is_sheriff:
                        counter[value] = count + 1.5
                    else:
                        counter[value] = count + 1
            if counter:
                max_vote = max(list(counter.values()))
                most_voted = sorted([k for k, v in counter.items() if v == max_vote])
            else:
                most_voted = []
            return {
                'vote_stage': vote_stage,
                'results': results,
                'most_voted': most_voted}


class Kill(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and user.is_host(room.name):
            parser = reqparse.RequestParser()
            parser.add_argument('seat', type=int)
            args = parser.parse_args()
            room.kill(args['seat'])
        return {'death': args['seat']}

class Sheriff(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id) and user.is_host(room.name):
            parser = reqparse.RequestParser()
            parser.add_argument('seat', type=int)
            args = parser.parse_args()
            room.set_sheriff(args['seat'])
        return {'death': args['seat']}

class Campaign(Resource):
    def post(self, room_name, user_id):
        user = User.query.filter_by(id=user_id).first()
        room = Room.query.filter_by(name=room_name).first()
        if room.has_user(user.id):
            parser = reqparse.RequestParser()
            parser.add_argument('seat', type=int)
            parser.add_argument('campaign', type=int)
            args = parser.parse_args()
            print(args)
            if args['campaign'] == 1:
                room.campaign(args['seat'])
                return {'campaign': True}
            else:
                room.quit_campaign(args['seat'])
                return {'campaign': False}

