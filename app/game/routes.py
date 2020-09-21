from collections import defaultdict
import pdb
from threading import Lock
from urllib.parse import unquote

from flask import render_template, redirect, url_for, request, \
    copy_current_request_context, session
from flask_login import current_user, login_required
from flask_restful import Api
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from app import socketio, db
from app.forms import TemplateForm
from app.game import bp
from app.models import User, Game, Player, GameTemplate
from app.game.tools import random_with_n_digits, generate_game_token, \
    check_game_token, check_socketio_message
from app.game.apis import Template



@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = TemplateForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            room_name = random_with_n_digits()
            template = GameTemplate.objects(name=form.template.data).first()
            game = Game(template=template, room_name=room_name)
            game.host = User.objects(id=current_user.id).first()
            game.save()

            return redirect(url_for('game.game', room_name=room_name))
    return render_template('game/setup.html', title='设置游戏', form=form)


@bp.route('/game/<room_name>', methods=['GET', 'POST'])
@login_required
def game(room_name):
    if current_user.is_authenticated:
        game = Game.objects(room_name=room_name).first()
        token = generate_game_token(user=current_user, game=game)
        return render_template('game/room.html', title='游戏进行中', game=game, token=token)
    else:
        return redirect(url_for('auth.login'))

# apis
api = Api(bp)
api.add_resource(Template, '/template/<template_name>')

# SocketIO apis
# TODO: Refactor later, need to make emit centralized

thread = None
thread_lock = Lock()


@socketio.on('connect', namespace='/game')
def test_connect():
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('join', namespace='/game')
def join(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    if game.has_user(user.id):
        join_room(game.room_name) # use room to define room id

        # check if user is seated
        if game.has_host(user.id):
            your_character = '上帝'
            emit('characters', {
                'characters': game.player_characters(user.id),
            })
        else:
            role = game.current_player_of(user.id)
            print(role.id)
            if role.is_seated:
                emit('seated', {'seat': role.seat})
                your_character = role.character or '等待分发'
                seated_room_name = f"{game.room_name}-seated"
                join_room(seated_room_name)
            else:
                audience_room_name = f"{game.room_name}-audience"
                join_room(audience_room_name)
                your_character = '等待分发'
                # send available seats to audience only
                # TODO: Combine this with characters
                emit('available_seats', {
                    'seats': game.available_seats}, room=audience_room_name)

            # separate characters from the other information
            # so that only host could see all characters
            # TODO: merge this with seats
            file_name = f"character_logo/{your_character}.png"
            chracter_url = unquote(url_for('static', filename=file_name))
            emit('player_character', {
                'your_character': your_character,
                'character_url': chracter_url
            })

        emit('game_status',
            {'data': game.description}, room=game.room_name)

        # vote_status
        emit('vote_status', {
            'vote_status': game.vote_status,
            'player_vote_status': game.player_vote_status,
            'candidates': game.vote_candidates
        }, room=game.room_name)

        # vote results
        if game.current_stage != '准备阶段':
            emit('vote_results', game.view_vote_results(game.current_stage), room=game.room_name)
        

        if game.current_stage == "警长竞选":
            emit('campaign_status', {
                'campaign_status': game.campaign_status,
            }, room=game.room_name)

            emit('campaign_candidates', game.campaign_players, room=game.room_name)

        emit('character_status', {
                'locked': game.character_locked,
            }, room=game.room_name)
        
        # for debug
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
            {'data': f'In rooms: {", ".join(rooms())}',
            'count': session['receive_count']}, room=game.room_name)


@socketio.on('character_assignment', namespace='/game')
def character_assignment(message):
    room_name = message['room_name']
    user = User.objects(id=message['user_id']).first()
    game = Game.objects(room_name=room_name).first()
    if not check_game_token(user, game, message['token']):
        return False

    if game.has_user(user.id):
        if message['fetch_characters']:
            pass
        else:
            if message['assign_characters']:
                room.assign_characters()
                # broadcast update
                emit('character_status', {
                    'locked': room.game.character_locked,
                }, room=game.room_name)
            else:
                success = room.lock_characters()
                emit('character_status', {
                    'locked': room.game.character_locked,
                }, room=game.room_name)

            data = {'data': room.description, 'locked': room.game.character_locked}
            emit('game_status', data, room=game.room_name)
            emit('characters', {'characters': room.player_characters(user)})
    else:
        role = user.current_role(room.name)
        your_character = role.character or '等待分发'
        file_name = f"character_logo/{your_character}.png"
        chracter_url = unquote(url_for('static', filename=file_name))
        emit('player_character', {
                'your_character': your_character,
                'character_url': chracter_url
        })


@socketio.on('round_assignment', namespace='/game')
def round_assignment(message):
    room_name = message['room_name']
    user = User.objects(id=message['user_id']).first()
    game = Game.objects(room_name=room_name).first()
    if not check_game_token(user, game, message['token']):
        return False

    if game.has_user(user.id):
        room.set_round(message['round_name'])

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('game_stage', {'stage': room.round}, room=game.room_name)


@socketio.on('vote_setup', namespace='/game')
def vote_setup(message):
    room_name = message['room_name']
    user = User.objects(id=message['user_id']).first()
    game = Game.objects(room_name=room_name).first()
    if not check_game_token(user, game, message['token']):
        return False

    if game.has_user(user.id):
        if message['allow_vote']:
            room.allow_votes()
            emit('vote_status', {
                'vote_status': room.vote_status,
                'player_vote_status': room.player_vote_status,
                'candidates': room.vote_candidates
            }, room=game.room_name)
        else:
            room.disable_votes()
            results = room.view_vote_results(room.round)
            emit('vote_status', {
                'vote_status': room.vote_status,
                }, room=game.room_name)
            
            # NOTE: prettify vote results
            # This should be done in frontend but I'm so bad at js :(
            
            emit('vote_results', results,
                room=game.room_name)
    else:
        pass
        # TODO: should make this an endpoint for checking vote results


@socketio.on('vote_for', namespace='/game')
def vote_for(message):
    room_name = message['room_name']
    user = User.objects(id=message['user_id']).first()
    game = Game.objects(room_name=room_name).first()
    if not check_game_token(user, game, message['token']):
        return False

    if game.has_user(user.id):
        role = user.current_role(room.name)
        if role.capable_for_vote:
            check = role.vote_for(message['vote_for'])
            if check[0]:
                emit('vote_success', {'vote_for': check[-1]})
            else:
                emit('vote_failure', {'error_message': '投票失败'})
        else:
            emit('vote_failure', {'error_message': '本轮不可投票'})


@socketio.on('sit_down', namespace='/game')
def sit_down(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    audience_room_name = f"{game.room_name}-audience"
    if game.has_audience(user.id):
        role = game.current_player_of(user.id)
        seat = int(message['seat'])
        success = role.sit_at(seat)
        if success:
            emit('available_seats', {'seats': game.available_seats}, room=audience_room_name)
            leave_room(audience_room_name)
            emit('seated', {'seat': role.seat})
            seated_room_name = f"{game.room_name}-seated"
            join_room(seated_room_name)

    data = {'data': game.description, 'locked': game.character_locked}
    emit('game_status', data, room=game.room_name)


@socketio.on('campaign_setup', namespace='/game')
def campaign_setup(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    if game.has_user(user.id):
        if message['allow_campaign']:
            room.set_round("警长竞选")
            room.allow_campaign()
        else:
            room.set_round("警长竞选")
            room.disable_campaign()
        emit('campaign_status', {
            'campaign_status': room.campaign_status,
        }, room=game.room_name)

        emit('campaign_candidates', room.campaign_players, room=game.room_name)


@socketio.on('sheriff_campaign', namespace='/game')
def sheriff_campaign(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    if game.has_user(user.id):
        role = user.current_role(room.name)
        # Only allow seated players to vote
        if role.is_seated:
            # campaign = True means in campaign
            # False means quitting campaign
            if message['campaign']:
                success = role.campaign()
                emit('campaign_registry', {
                    'seat': role.seat, 
                    'success': success
                })
            else:
                success = role.quit_campaign()
                emit('campaign_quit', {
                    'seat': role.seat, 
                    'success': success
                })
        emit('campaign_candidates', room.campaign_players, room=game.room_name)


@socketio.on('sheriff_badge', namespace='/game')
def sheriff_badge(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    if game.has_user(user.id):
        seat = message['seat']
        success = room.set_sheriff(seat)
        emit('badge_status', {
            'success': success,
            'sheriff': room.sheriff
        })

        # update sheriff by emitting game_status
        data = {'data': room.description, 'locked': room.game.character_locked}
        emit('game_status', data, room=game.room_name)


@socketio.on('player_death', namespace='/game')
def player_death(message):
    check = check_socketio_message(message)
    if not check:
        return False, 404
    
    user, game = check
    if game.has_user(user.id):
        seat = message['seat']
        if message['method'] == '复活':
            success = room.revive(seat)
        else:
            success = room.kill(seat, method=message['method'])
        emit('death_status', {
            'success': success,
            'seat': seat
        })

        # update sheriff by emitting game_status
        data = {'data': room.description, 'locked': room.game.character_locked}
        emit('game_status', data, room=game.room_name)


@socketio.on('leave', namespace='/game')
def leave(message):
    leave_room(game.room_name)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/game')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + game.room_name + ' is closing.',
                         'count': session['receive_count']},
         room=game.room_name)
    close_room(game.room_name)


@socketio.on('disconnect_request', namespace='/game')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.on('my_ping', namespace='/game')
def ping_pong():
    emit('my_pong')


@socketio.on('disconnect', namespace='/game')
def test_disconnect():
    print('Client disconnected', request.sid)