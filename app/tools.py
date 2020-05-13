from random import randint


GAME_ID_LENGTH = 6


def random_with_N_digits(n=GAME_ID_LENGTH):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)