from flask import render_template, abort

from app.character import bp
from app.tools import CHARACTER_INTRO


# TODO: make this restful api and add to db
# also should make a systematic way of adding
# character in admin view
@bp.route('/character_intros')
def character_intros():
    characters = CHARACTER_INTRO
    return render_template('character/characters.html', characters=characters)

@bp.route('/character_page/<character_name>', methods=['GET'])
def character_page(character_name):
    character = [c for c in CHARACTER_INTRO if c['名字']==character_name]
    if character:
        return render_template('character/character_page.html', character=character[0])
    else:
        abort(404, "这个角色不存在")
