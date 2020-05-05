from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Game

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class VoteForm(FlaskForm):
    votefor = StringField('Votefor', validators=[DataRequired()])
    submit = SubmitField('Vote')

    def validate_votefor(self, votefor):
        votefor_id = int(votefor.data)
        if votefor_id > 12 or votefor_id < 0:
            raise ValidationError('Please vote for a number in between 0 and 12.')


class RoleForm(FlaskForm):
    role_opts = [('God', 'God'), ('Player', 'Player'), ('Audience', 'Audience')]
    role = SelectField('Role', choices=role_opts)
    submit = SubmitField('Submit')


class PlayerPregameForm(FlaskForm):
    seat = StringField('Seat', validators=[DataRequired()])
    submit = SubmitField('Enter Game')

    def validate_seat(self, seat):
        seat_id = int(seat.data)
        if seat_id > 12 or seat_id < 1:
            raise ValidationError('Please fill with your seat number in between 1 and 12.')


class PregameForm(FlaskForm):
    game_name = StringField('Game Name', validators=[DataRequired()])
    submit = SubmitField('Start Game')


class GameForm(FlaskForm):
    
    round_opts = [
        ('警长竞选', '警长竞选'),
        ('警长竞选-pk', '警长竞选-pk'),
        ('第1天放逐', '第1天放逐'),
        ('第1天放逐-pk', '第1天放逐-pk'),
        ('第2天放逐', '第2天放逐'),
        ('第2天放逐-pk', '第2天放逐-pk'),
        ('第3天放逐', '第3天放逐'),
        ('第3天放逐-pk', '第3天放逐-pk'),
        ('第4天放逐', '第4天放逐'),
        ('第4天放逐-pk', '第4天放逐-pk'),
        ('第5天放逐', '第5天放逐'),
        ('第5天放逐-pk', '第5天放逐-pk')
    ]
    current_round = SelectField('Round', choices=round_opts, validate_choice=False)
    submit = SubmitField('Start Vote')
    

class ViewForm(FlaskForm):
    view = SubmitField('View Vote')


class EndGameForm(FlaskForm):
    end = SubmitField('End Game')
