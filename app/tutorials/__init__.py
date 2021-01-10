from flask import Blueprint

bp = Blueprint('tutorials', __name__)

from app.tutorials import routes