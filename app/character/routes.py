from flask import render_template, abort

from app.models import Character
from app.character import bp


# TODO: make this restful api and add to db
# also should make a systematic way of adding
# character in admin view
@bp.route('/character_intros')
def character_intros():
    characters = Character.objects()
    return render_template('character/characters.html', characters=characters)

@bp.route('/character_page/<character_id>', methods=['GET'])
def character_page(character_id):
    character = Character.objects(id=character_id).first()
    if character:
        return render_template('character/character_page.html', character=character)
    else:
        abort(404, "这个角色不存在")
