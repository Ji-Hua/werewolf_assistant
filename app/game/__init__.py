from flask import Blueprint

bp = Blueprint('game', __name__)

from app.game import routes