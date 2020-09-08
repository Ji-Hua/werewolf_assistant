from urllib.parse import unquote

from flask import render_template, flash, redirect, url_for, request, \
    jsonify, copy_current_request_context, session
from flask_login import current_user, login_user, logout_user, login_required

from werkzeug.urls import url_parse

from app import db, login
from app.forms import CreateGameForm
from app.main import bp
from app.models import User, Room, Player

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = CreateGameForm()
    if current_user.is_authenticated:
        if form.validate():
            if form.create_game.data:
                next_page = url_for('game.setup')
                return redirect(next_page)
            if form.enter_game.data:
                # TODO: should validate room_name here
                room = Room.query.filter_by(name=form.room_name.data).first()
                player = Player(user_id=current_user.id, room_id=room.id, is_host=False)
                db.session.add(player)
                db.session.commit()
                next_page = url_for('game.room', room_name=room.name)
            return redirect(next_page)
        
    return render_template('index.html', title='首页', form=form)

