from typing import NamedTuple


class Skill(NamedTuple):
    name: str
    intro: str

    def __repr__(self):
        return f"{self.name}: {self.intro}"
