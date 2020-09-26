from app import db


class Player(db.Document):
    user = db.ReferenceField('User')
    game = db.ReferenceField('Game')
    character = db.ReferenceField('Character')
    seat_at = db.IntField()

    # death related
    # death_method could be 死亡（夜间死亡）, 放逐(白天公投), 自爆，枪杀，决斗，殉情
    is_dead = db.BooleanField(required=True, default=False)
    death_status = db.StringField(default='存活')

    # sheriff campaign
    is_sheriff = db.BooleanField(default=False)
    in_sheriff_campaign = db.BooleanField(default=False)
    sheriff_campaigned = db.BooleanField(default=False)

    # vote related
    is_candidate = db.BooleanField(default=True)
    capable_to_vote = db.BooleanField(default=True)

    @property
    def seat(self):
        return self.seat_at or 0

    @seat.setter
    def seat(self, seat):
        if int(seat) not in self.game.valid_seats:
            raise Exception(f"invalid seat {seat}")
        self.seat_at = seat
        self.save()

    @property
    def is_seated(self):
        return (self.seat in self.game.valid_seats)

    @property
    def death_status(self):
        if self.is_dead:
            return self.death_status
        else:
            return "存活"

    @property
    def sheriff_campaign_status(self):
        if self.in_sheriff_campaign:
            return 'campaign'
        else:
            if self.sheriff_campaigned:
                return 'quit'
            else:
                return 'uncampaign'

    @property
    def description(self):
        description = {
            "seat": int(self.seat),
            "name": self.user.username,
            "death": self.death_status,
            "is_sheriff": self.is_sheriff,
            "in_campaign": self.in_sheriff_campaign,
            "campaigned": self.sheriff_campaigned
        }
        return description
    
    def _sit_at(self, seat):
        if self.is_seated:
            return False
        elif seat not in self.game.available_seats:
            return False
        else:
            self.seat = seat
            return True

    def sit_at(self, seat):
        if self._sit_at(seat):
            self.save()
            self.game.seat_player(self)
            return True
        else:
            return False

    def die(self, death_method='死亡'):
        self.death_status = death_method
        self.is_dead = True
        self.is_sheriff = False
        self.save()

    def revive(self):
        self.death_status = '存活'
        self.is_dead = False
        self.save()

    def set_character(self, character_id):
        self.character = character_id
        self.save()

    def become_sheriff(self):
        self.is_sheriff = True
        self.save()

    def retire_sheriff(self):
        self.is_sheriff = False
        self.save()
