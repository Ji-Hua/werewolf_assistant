import random
from typing import Dict, List, NamedTuple, Optional


class GameTemplate:

    def __init__(self, name: str, 
            characters: Dict[str, int]):
        self.name = name
        self.characters = characters
        self.player_number = sum(self.characters.values())

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