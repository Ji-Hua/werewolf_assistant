import os

from app import create_app, db
from app.models import User, Game, Player, GameTemplate, Skill, Character

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Game': Game,
        'Player': Player, 'GameTemplate': GameTemplate, 'Skill': Skill,
        'Character': Character}