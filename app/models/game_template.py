from app import db

class GameTemplate(db.Document):
    name = db.StringField(required=True, unique=True)
    player_number = db.IntField(required=True, default=12)
    characters = db.DictField(required=True)

    @property
    def description(self):
        text = f"{self.name} ({self.player_number} 人): \n"
        for key, value in self.characters.items():
            text += f"{key}x{value}\n"
        return text
