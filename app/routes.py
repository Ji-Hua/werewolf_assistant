from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db, api
from app.email import send_password_reset_email
from app.forms import (LoginForm, RegistrationForm, CreateGameForm, 
    GameRoundForm, SeatForm,TemplateForm, ResetPasswordRequestForm,
    ResetPasswordForm)
from app.models import User, Vote, Game, Room, Player
from app.tools import random_with_n_digits, assign_character
from app.apis import Table, Seat, Character, Round, Votes, Kill, Sheriff, Campaign


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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('请查看邮件')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('密码已经重置')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


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
            room_name = random_with_n_digits()
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
            return render_template('room.html', title='游戏进行中', room=room)
    else:
        return redirect(url_for('login'))


# APIs
# TODO: use flask-restful later

api.add_resource(Table, '/room/<room_name>/<user_id>/seats')
api.add_resource(Seat, '/room/<room_name>/<user_id>/seat')
api.add_resource(Round, '/room/<room_name>/<user_id>/round')
api.add_resource(Character, '/room/<room_name>/<user_id>/character')
api.add_resource(Votes, '/room/<room_name>/<user_id>/vote')
api.add_resource(Kill, '/room/<room_name>/<user_id>/kill')
api.add_resource(Sheriff, '/room/<room_name>/<user_id>/sheriff')
api.add_resource(Campaign, '/room/<room_name>/<user_id>/campaign')

@app.route('/static/character_logo/<filename>')
def send_image(filename):
    return send_from_directory("static/character_logo", filename)

@app.route('/room/<room_name>/<user_id>/character_image', methods=['GET'])
def character_image(room_name, user_id):
    user = User.query.filter_by(id=user_id).first()
    room = Room.query.filter_by(name=room_name).first()
    if room.has_user(user.id) and not user.is_host(room.name):
        player = user.current_role(room.name)
        if player.character:
            character = player.character
        else:
            character = '等待分发'
        
        return send_image(f"{character}.png")

    
# @app.route('/room/<room_name>/candidates', methods=['GET'])
# @login_required
# def candidates(room_name):
#     room = Room.query.filter_by(name=room_name).first()
#     if room.round == "警长竞选":
#         candidates = [p.seat for p in room.survivals if p.in_sheriff_campaign and p.is_candidate]
#     else:
#         candidates = [p.seat for p in room.survivals if p.is_candidate]
#     return jsonify({'candidates': candidates})
