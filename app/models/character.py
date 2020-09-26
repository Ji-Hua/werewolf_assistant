from app import db

from .skill import Skill


class Character(db.Document):
    name = db.StringField(required=True, unique=True)
    name_en = db.StringField(null=True)
    camp = db.ListField(db.StringField(), required=True)
    skills = db.ListField(db.EmbeddedDocumentField(Skill))
    image = db.FileField()
    note = db.StringField()
    backgroud_story = db.StringField()

    def __repr__(self):
        return f"<Character {self.name}>"
