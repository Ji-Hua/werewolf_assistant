from flask import render_template

from app.character import bp
from app.tools import CHARACTER_INTRO


# TODO: make this restful api and add to db
# also should make a systematic way of adding
# character in admin view
@bp.route('/character_intros')
def character_intros():
    return render_template('character/characters.html', characters=CHARACTER_INTRO)

@bp.route('/character_page/<character_id>', methods=['GET'])
def character_page(character_id):
    data = None
    cis = []
    for k in CHARACTER_INTRO:
        cis.extend(CHARACTER_INTRO[k])
    for ci in cis:
        if ci['id'] == character_id:
            data = ci
            return render_template('character/character_page.html', data=data)
    else:
        raise ValueError("No such character")
