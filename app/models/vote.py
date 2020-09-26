from app import db


class Vote(db.EmbeddedDocument):
    vote_from = db.IntField(required=True)
    vote_for = db.IntField()
    abstention = db.BooleanField(default=False)