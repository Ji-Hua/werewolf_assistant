from typing import Dict, List, NamedTuple, Optional

class Vote(NamedTuple):
    vote_from: int
    vote_for: Optional[int] = 0

    def __eq__(self, other):
        return (self.vote_from == other.vote_from) \
            and (self.vote_for == other.vote_for)
    
    def __repr__(self):
        return f"Vote: {self.vote_from} --> {self.vote_for}"