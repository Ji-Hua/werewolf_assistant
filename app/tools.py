import random
from app.models import Room

GAME_ID_LENGTH = 6


def random_with_N_digits(n=GAME_ID_LENGTH):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)

GAME_TEMPLATES = {
    '预女猎白': {
        '预言家': 1,
        '女巫': 1,
        '白痴': 1,
        '猎人': 1,
        '狼人': 4,
        '村民': 4
    }
}

def build_character_queue(template_name):
    queue = []
    character_dict = GAME_TEMPLATES[template_name]
    for key, value in character_dict.items():
        for _ in range(value):
            queue.append(key)
    random.shuffle(queue)
    return queue
    


def assign_character(room_id):
    room = Room.query.filter_by(name=room_id).first()
    seated_players = room.normal_players()
    char_queue = build_character_queue(room.template)
    for p in seated_players:
        char_queue.pop(a.index(p.character))
    return char_queue[0]