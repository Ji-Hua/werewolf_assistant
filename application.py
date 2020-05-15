from app import app, db
from app.models import User, Vote, Game, Room, Player

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Vote': Vote, 'Game': Game, 'Player': Player, 'Room': Room}