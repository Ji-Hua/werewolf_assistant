from typing import NamedTuple


class Skill(NamedTuple):
    name: str
    introduction: str

    def __repr__(self):
        return f"{self.name}: {self.introduction}"
