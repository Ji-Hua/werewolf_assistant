import os

from flask_script import Manager, Shell

from app import create_app, db
from app.models import User, Game, Player, GameTemplate, Skill, Character, Vote

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Game': Game,
        'Player': Player, 'GameTemplate': GameTemplate, 'Skill': Skill,
        'Character': Character, 'Vote': Vote}

manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
