from typing import List, NamedTuple, Optional
from .skill import Skill


class Character(NamedTuple):
    name: str
    camp: List[str]
    skills: Optional[List[Skill]] = []
    lines: Optional[str] = ''
    background: Optional[str] = ''
    note: Optional[str] = ''
