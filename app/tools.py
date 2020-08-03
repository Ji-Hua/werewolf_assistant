import json
import os
import random

from app.models import Room

GAME_ID_LENGTH = 6


def random_with_N_digits(n=GAME_ID_LENGTH):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)

data_path = os.path.join(os.path.dirname(__file__), 'data/')
with open(os.path.join(data_path, 'game_config.json')) as f:
    GAME_TEMPLATES = json.load(f)

with open(os.path.join(data_path, 'character_intro.json')) as f:
    CHARACTER_INTRO = json.load(f)    

def build_character_queue(template_name):
    queue = []
    character_dict = GAME_TEMPLATES[template_name]
    for key, value in character_dict.items():
        for _ in range(value):
            queue.append(key)
    random.shuffle(queue)
    return queue
    

def assign_character(room_name):
    room = Room.query.filter_by(name=room_name).first()
    char_queue = build_character_queue(room.template)
    seated_players = room.seated_players
    if seated_players:
        for p in seated_players:
            char_queue.pop(char_queue.index(p.character))
    return char_queue[0]