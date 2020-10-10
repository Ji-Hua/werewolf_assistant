import json
import os
import random

GAME_ID_LENGTH = 4


def random_with_n_digits(n=GAME_ID_LENGTH):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)

data_path = os.path.join(os.path.dirname(__file__), 'data/')
with open(os.path.join(data_path, 'game_config.json')) as f:
    GAME_TEMPLATES = json.load(f)

with open(os.path.join(data_path, 'character_intro.json')) as f:
    CHARACTER_INTRO = json.load(f)    
