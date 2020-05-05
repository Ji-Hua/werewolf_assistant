from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, VoteForm, RoleForm, \
    PregameForm, GameForm, PlayerPregameForm, ViewForm, EndGameForm
from app.models import User, Vote, Game

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = RoleForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            current_user.role = form.role.data
            db.session.commit()
            next_page = url_for('pregame')
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


@app.route('/vote/<username>', methods=['GET', 'POST'])
@login_required
def vote(username):
    if current_user.is_authenticated:
        game = Game.query.filter_by(is_active=True).order_by(
            Game.id.desc()).limit(1).all()[0]
        end_game_form = EndGameForm()
        view_form = ViewForm()
        if current_user.role == 'God':
            form = GameForm()
            if form.validate() and form.submit.data:
                game.current_round = form.current_round.data
                db.session.commit()
                flash(f"Vote of {form.current_round.data} began")
            
            if end_game_form.validate() and end_game_form.end.data:
                game.end()
                db.session.commit()
                users = User.query.all()
                for user in users:
                    user.seat = -1
                    db.session.commit()
                return redirect(url_for('pregame'))
        else:
            form = VoteForm()
            if form.validate() and form.submit.data:
                flash(f"{current_user.seat} voted for {form.votefor.data}")
                v = Vote(seat=current_user.seat, game_id=game.id,
                    round=game.current_round, vote_for=form.votefor.data,
                    player=current_user)
                db.session.add(v)
                db.session.commit()
                return redirect(url_for('pregame'))
        
        if view_form.validate() and view_form.view.data:
            votes = Vote.query.filter_by(game_id=game.id).filter_by(round=game.current_round).all()
            flash(game.id)
            flash(game.current_round)
            flash(votes)

        return render_template('vote.html', title='Vote', form=form, game=game,
            end_game_form=end_game_form, view_form=view_form)
    else:
        return redirect(url_for('login'))



@app.route('/pregame', methods=['GET', 'POST'])
@login_required
def pregame():
    if current_user.is_authenticated:
        if current_user.role == 'God':
            form = PregameForm()
            if form.validate_on_submit():
                game = Game(name=form.game_name.data, host=current_user.id)
                db.session.add(game)
                db.session.commit()
                flash(f'{game.name} started')
                return redirect(url_for('vote', username=current_user.username))
        else:
            form = PlayerPregameForm()
            if form.validate_on_submit():
                if current_user.seat == 0:
                    current_user.seat = int(form.seat.data)
                    db.session.commit()
                return redirect(url_for('vote', username=current_user.username))
        return render_template('pregame.html', title='Pregame', form=form, current_user=current_user)
    else:
        return redirect(url_for('login'))
