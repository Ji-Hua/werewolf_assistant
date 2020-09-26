from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

class User(UserMixin, db.Document):
    # TODO: Add game related documents
    # TODO: should make query like user.find_by_id as a method in order to
    # decouple db from model
    email = db.EmailField(required=True, unique=True, null=False)
    username = db.StringField(required=True, unique=True, null=False)
    password_hash = db.StringField(required=True)
    confirmed = db.BooleanField(default=False)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'email': str(self.email)})

    def verify_confirmation_token(self, token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except:
            return False
        if data.get('email') != str(self.email):
            return False
        return True

    def confirm(self, token):
        if self.verify_confirmation_token(token):
            self.confirmed = True
            self.save()
        return self.confirmed

    def generate_reset_password_token(self, expiration=600):
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'reset_password': str(self.email)})

    @staticmethod
    def read_reset_password_token(token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token)['reset_password']
        except:
            return
        return email

    @staticmethod
    def query_user_by_reset_password_token(token):
        data = User.read_reset_password_token(token)
        return data and User.objects(email=data).first()

# NOTE: Flask-login needs a callback function to load user
# with a unique id
@login.user_loader
def load_user(user_id):
    return User.objects(id=str(user_id)).get()
