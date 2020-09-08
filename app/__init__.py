import logging
from logging.handlers import SMTPHandler

from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_restful import Api
from flask_socketio import SocketIO

from config import config

api = Api()
db = SQLAlchemy()
login = LoginManager()
# login view should be the right login function
login.login_view = 'auth.login'
mail = Mail()
socketio = SocketIO()


def create_app(config_name):
    """ A factory function to create instance

    Return an instance of application with configuations passed in
    """
    app = Flask(__name__)
    # read environment config from config.py
    app.config.from_object(config[config_name])

    # init components
    api.init_app(app)

    db.init_app(app)
    migrate = Migrate(app, db) # update migrate

    login.init_app(app)

    mail.init_app(app)

    socketio.init_app(app)

    # routes and error handling
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.game import bp as game_bp
    app.register_blueprint(game_bp)

    from app.character import bp as character_bp
    app.register_blueprint(character_bp)

    return app

from app import models