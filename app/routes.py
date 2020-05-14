from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import (LoginForm, RegistrationForm, VoteForm, CreateGameForm, 
    PregameForm, GameForm, SeatForm, ViewForm, EndGameForm, TemplateForm)
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
                # TODO: should validate room_id here
                room_id = form.room_id.data
                player = Player(user_id=current_user.id, room_id=room_id)
                db.session.add(player)
                db.session.commit()
                next_page = url_for('room', room_id=room_id)
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
            room_id = random_with_N_digits()
            room = Room(name=room_id, host=current_user.id)
            db.session.add(room)
            db.session.commit()
            game = Game(template=form.template.data, room_id=room.id)
            db.session.add(game)
            player = Player(user_id=current_user.id, room_id=room.id, is_host=True)
            db.session.add(player)
            db.session.commit()
            next_page = url_for('room', room_id=room_id)
            return redirect(next_page)
    return render_template('setup.html', title='设置游戏', form=form)


@app.route('/room/<room_id>', methods=['GET', 'POST'])
@login_required
def room(room_id):
    if current_user.is_authenticated:
        room = Room.query.filter_by(name=room_id).first()
        if current_user.is_host:
            return render_template('room.html', title='游戏进行中', room=room)
        else:
            if current_user.current_role(room_id).is_seated:
                pass
                return render_template('room.html', title='游戏进行中', room=room)
            else:
                seat_form = SeatForm()
                if seat_form.is_submitted():
                    role = current_user.current_role(room_id)
                    role.seat = int(seat_form.seat.data)
                    role.character = assign_character(room_id)
                    db.session.commit()
                
                return render_template('room.html', title='游戏进行中', room=room, seat_form=seat_form)
    else:
        return redirect(url_for('login'))



@app.route('/vote/<username>', methods=['GET', 'POST'])
@login_required
def vote(username):
    pass


# APIs
@app.route('/room/<room_id>/seats', methods=['GET'])
@login_required
def seats(room_id):
    room = Room.query.filter_by(name=room_id).first()
    return jsonify({'seats': list(room.available_seats)})