from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db, api
from app.forms import (LoginForm, RegistrationForm, CreateGameForm, 
    GameRoundForm, SeatForm,TemplateForm)
from app.models import User, Vote, Game, Room, Player
from app.tools import random_with_n_digits, assign_character
from app.apis import Table, Seat, Character, Round



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = CreateGameForm()
    if current_user.is_authenticated:
        if form.validate():
            if form.create_game.data:
                next_page = url_for('setup')
                return redirect(next_page)
            if form.enter_game.data:
                # TODO: should validate room_name here
                room = Room.query.filter_by(name=form.room_name.data).first()
                player = Player(user_id=current_user.id, room_id=room.id, is_host=False)
                db.session.add(player)
                db.session.commit()
                next_page = url_for('room', room_name=room.name)
            return redirect(next_page)
        
    return render_template('index.html', title='首页', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('密码或用户名不正确')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='登录', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功')
        return redirect(url_for('login'))
    return render_template('register.html', title='注册', form=form)


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = TemplateForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            room_name = random_with_N_digits()
            room = Room(name=room_name)
            db.session.add(room)
            db.session.commit()
            game = Game(template=form.template.data, room_id=room.id)
            db.session.add(game)
            player = Player(user_id=current_user.id, room_id=room.id, is_host=True)
            db.session.add(player)
            db.session.commit()
            next_page = url_for('room', room_name=room_name)
            return redirect(next_page)
    return render_template('setup.html', title='设置游戏', form=form)


@app.route('/room/<room_name>', methods=['GET', 'POST'])
@login_required
def room(room_name):
    if current_user.is_authenticated:
        room = Room.query.filter_by(name=room_name).first()
        if current_user.is_host(room.name):
            form = GameRoundForm()
            return render_template('room.html', title='游戏进行中', room=room, form=form)
        else:
            role = current_user.current_role(room_name)
            db.session.commit()
            return render_template('room.html', title='游戏进行中', room=room)
    else:
        return redirect(url_for('login'))


# APIs
# TODO: use flask-restful later

api.add_resource(Table, '/room/<room_name>/<user_id>/seats')
api.add_resource(Seat, '/room/<room_name>/<user_id>/seat')
api.add_resource(Round, '/room/<room_name>/<user_id>/round')
api.add_resource(Character, '/room/<room_name>/<user_id>/character')

@app.route('/room/<room_name>/<user_id>/game_status', methods=['GET'])
@login_required
def game_status(room_name, user_id):
    room = Room.query.filter_by(name=room_name).first()
    return jsonify({'status': room.game.status})

# @app.route('/room/<room_name>/available_seats', methods=['GET'])
# @login_required
# def available_seats(room_name):
#     room = Room.query.filter_by(name=room_name).first()
#     return jsonify({'seats': room.available_seats})


@app.route('/room/<room_name>/vote', methods=['POST'])
@login_required
def vote(room_name):
    player = Player.query.filter_by(id=int(request.form['player_id'])).first()
    if player.capable_for_vote:
        game = Room.query.filter_by(name=room_name).first().game
        vote_for = int(request.form['vote_for'])
        if vote_for <= 0 or vote_for > 12:
            vote_for = 0
        round = request.form['round']
        prev_votes = Vote.query.filter_by(game_id=game.id, player_id=player.id, round=round).all()
        if prev_votes:
            for v in prev_votes:
                db.session.delete(v)
            db.session.commit()
        vote = Vote(game_id=game.id, player_id=player.id, vote_for=vote_for, round=round)
        db.session.add(vote)
        db.session.commit()
        player.capable_for_vote = False
        db.session.commit()
        return {"vote": vote_for}
    else:
        return {"vote": -1}
    
@app.route('/room/<room_name>/candidates', methods=['GET'])
@login_required
def candidates(room_name):
    room = Room.query.filter_by(name=room_name).first()
    if room.round == "警长竞选":
        candidates = [p.seat for p in room.survivals if p.in_sheriff_campaign and p.is_candidate]
    else:
        candidates = [p.seat for p in room.survivals if p.is_candidate]
    return jsonify({'candidates': candidates})

@app.route('/room/<room_name>/results/<round_name>', methods=['GET'])
@login_required
def results(room_name, round_name):
    room = Room.query.filter_by(name=room_name).first()
    results = room.view_vote_results(round_name)
    results = sorted(results, key=lambda x: x['vote_from'])
    counter = {}
    for row in results:
        value = row['vote_for']
        if value > 0 and value < 12:
            count = counter.get(value, 0)
            counter[value] = count + 1
    if counter:
        max_vote = max(list(counter.values()))
        most_voted = sorted([k for k, v in counter.items() if v == max_vote])
    else:
        most_voted = []
    return jsonify({'results': results, 'most_voted': most_voted})


@app.route('/room/<room_name>/campaign', methods=['POST'])
@login_required
def campaign(room_name):
    room = Room.query.filter_by(name=room_name).first()
    seat = int(request.form['seat'])
    if request.form['campaign'] == 'true':
        room.campaign(seat)
        return jsonify({'campaign': True})
    else:
        room.quit_campaign(seat)
        return jsonify({'campaign': False})

@app.route('/room/<room_name>/kill', methods=['POST'])
@login_required
def kill(room_name):
    room = Room.query.filter_by(name=room_name).first()
    seat = int(request.form['seat'])
    room.kill(seat)
    return jsonify({'killed': True})

@app.route('/room/<room_name>/sheriff', methods=['POST'])
@login_required
def sheriff(room_name):
    room = Room.query.filter_by(name=room_name).first()
    seat = int(request.form['seat'])
    room.set_sheriff(seat)
    return jsonify({'sheriff': seat})
