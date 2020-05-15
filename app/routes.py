from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import (LoginForm, RegistrationForm, VoteForm, CreateGameForm, 
    GameRoundForm, SeatForm, ViewForm, TemplateForm)
from app.models import User, Vote, Game, Room, Player
from app.tools import random_with_N_digits, assign_character



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
        
    return render_template('index.html', title='Home', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


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
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = TemplateForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            room_name = random_with_N_digits()
            room = Room(name=room_name, host=current_user.id)
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
        if current_user.is_host:
            form = GameRoundForm()
            return render_template('room.html', title='游戏进行中', room=room, form=form)
        else:
            if current_user.current_role(room_name).is_seated:
                return render_template('room.html', title='游戏进行中', room=room)
            else:
                seat_form = SeatForm()
                if seat_form.is_submitted():
                    role = current_user.current_role(room_name)
                    role.character = assign_character(room_name)
                    role.seat = int(seat_form.seat.data)
                    db.session.commit()
                
                return render_template('room.html', title='游戏进行中', room=room, seat_form=seat_form)
    else:
        return redirect(url_for('login'))


# APIs
# TODO: use flask-restful later

@app.route('/room/<room_name>/seats', methods=['GET'])
@login_required
def seats(room_name):
    room = Room.query.filter_by(name=room_name).first()
    return jsonify({'seats': room.available_seats})


@app.route('/room/<room_name>/game_status', methods=['GET'])
@login_required
def game_status(room_name):
    room = Room.query.filter_by(name=room_name).first()
    return jsonify({'status': room.game.status})


@app.route('/room/<room_name>/vote', methods=['POST'])
@login_required
def vote(room_name):
    player = Player.query.filter_by(id=int(request.form['player_id'])).first()
    if player.capable_for_vote:
        game = Room.query.filter_by(name=room_name).first().game
        vote_for = int(request.form['vote_for'])
        print(vote_for)
        if vote_for <= 0 or vote_for > 12:
            vote_for = 0
        round = request.form['round']
        vote = Vote(game_id=game.id, player_id=player.id, vote_for=vote_for, round=round)
        db.session.add(vote)
        db.session.commit()
        player.capable_for_vote = False
        db.session.commit()
        return {"vote": vote_for}
    else:
        return {"vote": 0}
    
    
@app.route('/room/<room_name>/round', methods=['POST'])
@login_required
def round(room_name):
    room = Room.query.filter_by(name=room_name).first()
    if request.form['allow_vote'] == 'true':
        round_name = request.form['round_name']
        room.set_round(round_name)
        room.allow_votes()
        return {'vote': 1}
    else:
        room.disable_votes()
        room.set_round('')
        return {'vote': 0}
    

@app.route('/room/<room_name>/candidates', methods=['GET'])
@login_required
def candidates(room_name):
    room = Room.query.filter_by(name=room_name).first()
    candidates = [p.seat for p in room.survivals]
    return jsonify({'candidates': candidates})

@app.route('/room/<room_name>/results/<round_name>', methods=['GET'])
@login_required
def results(room_name, round_name):
    room = Room.query.filter_by(name=room_name).first()
    results = room.view_vote_results(round_name)
    print(results)
    return jsonify({'results': results})

