from app import db


class Skill(db.EmbeddedDocument):
    name = db.StringField(required=True, null=False)
    introduction = db.StringField(required=True, null=False)
