from collections import defaultdict
from threading import Lock
from urllib.parse import unquote

from flask import render_template, redirect, url_for, request, \
    copy_current_request_context, session
from flask_login import current_user, login_user, logout_user, login_required
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from app import socketio, db
from app.forms import TemplateForm
from app.game import bp
from app.models import User, Vote, Game, Room, Player
from app.tools import random_with_n_digits, assign_character, CHARACTER_INTRO


@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = TemplateForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            room_name = random_with_n_digits()
            room = Room(name=room_name)
            db.session.add(room)
            db.session.commit()
            game = Game(template=form.template.data, room_id=room.id)
            db.session.add(game)
            player = Player(user_id=current_user.id, room_id=room.id, is_host=True)
            db.session.add(player)
            db.session.commit()
            return redirect(url_for('game.room', room_name=room_name))
    return render_template('game/setup.html', title='设置游戏', form=form)


@bp.route('/room/<room_name>', methods=['GET', 'POST'])
@login_required
def room(room_name):
    if current_user.is_authenticated:
        room = Room.query.filter_by(name=room_name).first()
        return render_template('game/room.html', title='游戏进行中', room=room)
    else:
        return redirect(url_for('auth.login'))

# SocketIO apis
# TODO: Refactor later, need to make emit centralized

thread = None
thread_lock = Lock()

# def background_thread():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         socketio.sleep(10)
#         count += 1
#         socketio.emit('my_response',
#                       {'data': 'Server generated event', 'count': count},
#                       namespace='/game')

@socketio.on('connect', namespace='/game')
def test_connect():
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('join', namespace='/game')
def join(message):
    room_name = message['room']
    user = User.query.filter_by(id=message['user_id']).first()
    room = Room.query.filter_by(name=room_name).first()

    if room.has_user(user.id):
        join_room(room_name) # use room to define room id

        # check if user is seated
        if user.is_host(room.name):
            your_character = '上帝'
            emit('characters', {
                'characters': room.player_characters(user),
            })
        else:
            role = user.current_role(room.name)
            if role.is_seated:
                emit('seated', {'seat': role.seat})
                your_character = role.character or '等待分发'
                seated_room_name = f"{room_name}-seated"
                join_room(seated_room_name)
            else:
                audience_room_name = f"{room_name}-audience"
                join_room(audience_room_name)
                your_character = '等待分发'
                    # send available seats to audience only
                emit('available_seats', {
                    'seats': room.available_seats}, room=audience_room_name)

            # separate characters from the other information
            # so that only host could see all characters
            file_name = f"character_logo/{your_character}.png"
            chracter_url = unquote(url_for('static', filename=file_name))
            emit('player_character', {
                'your_character': your_character,
                'character_url': chracter_url
            })

        emit('game_status',
            {'data': room.description}, room=room_name)

        # vote_status
        emit('vote_status', {
            'vote_status': room.vote_status,
            'player_vote_status': room.player_vote_status,
            'candidates': room.vote_candidates
        }, room=message['room'])

        # vote results
        if room.round is not None:
            emit('vote_results', room.view_vote_results(room.round), room=message['room'])
        

        if room.round == "警长竞选":
            emit('campaign_status', {
                'campaign_status': room.campaign_status,
            }, room=message['room'])

            emit('campaign_candidates', room.campaign_players, room=message['room'])

        emit('character_status', {
                'locked': room.game.character_locked,
            }, room=message['room'])
        
        # for debug
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
            {'data': f'In rooms: {", ".join(rooms())}',
            'count': session['receive_count']}, room=room_name)


@socketio.on('character_assignment', namespace='/game')
def character_assignment(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
        if message['fetch_characters']:
            pass
        else:
            if message['assign_characters']:
                room.assign_characters()
                # broadcast update
                emit('character_status', {
                    'locked': room.game.character_locked,
                }, room=message['room'])
            else:
                success = room.lock_characters()
                emit('character_status', {
                    'locked': room.game.character_locked,
                }, room=message['room'])

            data = {'data': room.description, 'locked': room.game.character_locked}
            emit('game_status', data, room=message['room'])
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
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
        room.set_round(message['round_name'])

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('game_stage', {'stage': room.round}, room=message['room'])


@socketio.on('vote_setup', namespace='/game')
def vote_setup(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
        if message['allow_vote']:
            room.allow_votes()
            emit('vote_status', {
                'vote_status': room.vote_status,
                'player_vote_status': room.player_vote_status,
                'candidates': room.vote_candidates
            }, room=message['room'])
        else:
            room.disable_votes()
            results = room.view_vote_results(room.round)
            emit('vote_status', {
                'vote_status': room.vote_status,
                }, room=message['room'])
            
            # NOTE: prettify vote results
            # This should be done in frontend but I'm so bad at js :(
            
            emit('vote_results', results,
                room=message['room'])
    else:
        pass
        # TODO: should make this an endpoint for checking vote results


@socketio.on('vote_for', namespace='/game')
def vote_for(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if room.has_user(user.id):
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
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    audience_room_name = f"{room_name}-audience"
    if room.has_user(user.id):
        role = user.current_role(room.name)
        seat = int(message['seat'])
        success = role.sit_at(seat)
        if success:
            emit('available_seats', {'seats': room.available_seats}, room=audience_room_name)
            leave_room(audience_room_name)
            emit('seated', {'seat': role.seat})
            seated_room_name = f"{room_name}-seated"
            join_room(seated_room_name)

    data = {'data': room.description, 'locked': room.game.character_locked}
    emit('game_status', data, room=message['room'])


@socketio.on('campaign_setup', namespace='/game')
def campaign_setup(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
        if message['allow_campaign']:
            room.set_round("警长竞选")
            room.allow_campaign()
        else:
            room.set_round("警长竞选")
            room.disable_campaign()
        emit('campaign_status', {
            'campaign_status': room.campaign_status,
        }, room=message['room'])

        emit('campaign_candidates', room.campaign_players, room=message['room'])


@socketio.on('sheriff_campaign', namespace='/game')
def sheriff_campaign(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if room.has_user(user.id):
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
        emit('campaign_candidates', room.campaign_players, room=message['room'])


@socketio.on('sheriff_badge', namespace='/game')
def sheriff_badge(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
        seat = message['seat']
        success = room.set_sheriff(seat)
        emit('badge_status', {
            'success': success,
            'sheriff': room.sheriff
        })

        # update sheriff by emitting game_status
        data = {'data': room.description, 'locked': room.game.character_locked}
        emit('game_status', data, room=message['room'])


@socketio.on('player_death', namespace='/game')
def player_death(message):
    user_id, room_name = message['user_id'], message['room']
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if user.is_host(room.name):
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
        emit('game_status', data, room=message['room'])


@socketio.on('leave', namespace='/game')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/game')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


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