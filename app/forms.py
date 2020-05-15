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
    votefor = StringField('投票给', validators=[DataRequired()])
    submit = SubmitField('提交投票')


class CreateGameForm(FlaskForm):
    room_name = StringField('房间号')
    create_game = SubmitField('创建游戏')
    enter_game = SubmitField('进入游戏')
    

class TemplateForm(FlaskForm):
    choices = [('预女猎白', '预女猎白')]
    template = SelectField('游戏设置', choices=choices)
    submit = SubmitField('开始游戏')


class SeatForm(FlaskForm):
    seat = SelectField('选择座位')
    submit = SubmitField('坐下')


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
