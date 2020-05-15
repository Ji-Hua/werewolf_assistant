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
        '猎人': 1,
        '白痴': 1,
        '狼人': 4,
        '村民': 4
    },
    '狐女猎白': {
        '狐狸': 1,
        '女巫': 1,
        '猎人': 1,
        '白痴': 1,
        '狼人': 4,
        '村民': 4
    },
    '天狗 vs 预女猎月': {
        '预言家': 1,
        '女巫': 1,
        '猎人': 1,
        '操纵月亮的女孩': 1,
        '狼人': 3,
        '天狗': 1,
        '村民': 4
    },
    '机械狼 vs 通女猎守': {
        '通灵师': 1,
        '女巫': 1,
        '猎人': 1,
        '守卫': 1,
        '狼人': 3,
        '机械狼': 1,
        '村民': 4
    },
    '恶魔 vs 预女猎守': {
        '预言家': 1,
        '女巫': 1,
        '猎人': 1,
        '守卫': 1,
        '狼人': 3,
        '恶魔': 1,
        '村民': 4
    },
    '狐仙 vs 预女猎阴': {
        '预言家': 1,
        '女巫': 1,
        '猎人': 1,
        '阴阳使者': 1,
        '狼人': 3,
        '狐仙': 1,
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
    

def assign_character(room_name):
    room = Room.query.filter_by(name=room_name).first()
    char_queue = build_character_queue(room.template)
    seated_players = room.seated_players
    if seated_players:
        for p in seated_players:
            char_queue.pop(char_queue.index(p.character))
    return char_queue[0]