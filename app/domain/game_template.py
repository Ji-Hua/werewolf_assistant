import random
from typing import Dict, List, NamedTuple, Optional


class GameTemplate:

    def __init__(self, name: str, 
            characters: Dict[str, int], player_number: int=12):
        self.name = name
        self.characters = characters
        self.player_number = player_number

        if sum(self.characters.values()) != self.player_number:
            raise ValueError(f'Number of characters does not match player_number')

    def __repr__(self):
        text = f"{self.name} ({self.player_number} 人): \n"
        for key, value in self.characters.items():
            text += f"{key}x{value}\n"
        return text

    def __eq__(self, other):
        for name, num in self.characters.items():
            if name not in other.characters:
                return False
            if num != other.characters[name]:
                return False
        return True

    @property
    def description(self):
        return self.__repr__()
    
    def shuffle_characters(self):
        queue = []
        for key, value in self.characters.items():
            for _ in range(value):
                queue.append(key)
        random.shuffle(queue)
        return queue