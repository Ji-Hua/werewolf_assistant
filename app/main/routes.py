from flask import render_template, redirect, url_for, abort
from flask_login import current_user, login_required

from werkzeug.urls import url_parse

from app import db, login
from app.forms import CreateGameForm
from app.main import bp
from app.models import User, Game, Player

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
                room_name = str(form.room_name.data)
                games = Game.objects(room_name=room_name)
                if games:
                    game = games.first()
                    # TODO: should move this to models
                    if not Player.objects(user=current_user.id, game=game):
                        player = Player(user=current_user.id, game=game).save()
                        game.audience.append(player)
                        game.save()
                    next_page = url_for('game.game', room_name=room_name)
                    return redirect(next_page)
                else:
                    abort(404, f"并未找到名为{room_name}的房间，请确认房间名称正确") 
            
        
    return render_template('index.html', title='首页', form=form)


# TODO: add logging and email
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html', error=e), 404

@bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html', error=e), 500
