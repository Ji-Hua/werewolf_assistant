from app import db

from .vote import Vote


class VoteResult(db.EmbeddedDocument):
    raw_votes = db.ListField(db.EmbeddedDocumentField(Vote))
    max_votes = db.ListField()
    vote_counts = db.DictField()
    votes_from = db.MapField(db.ListField())
    round = db.StringField()
