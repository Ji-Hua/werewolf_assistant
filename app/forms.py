from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Game
from app.tools import GAME_TEMPLATES

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    email = StringField('电子邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField(
        '重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('请使用其他用户名')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('请使用其他电子邮箱')


class CreateGameForm(FlaskForm):
    room_name = StringField('房间号')
    create_game = SubmitField('创建游戏')
    enter_game = SubmitField('进入游戏')
    

class TemplateForm(FlaskForm):
    choices = [(key, key) for key in GAME_TEMPLATES.keys()]
    template = SelectField('游戏设置', choices=choices)
    submit = SubmitField('开始游戏')


class SeatForm(FlaskForm):
    seat = SelectField('选择座位')
    submit = SubmitField('坐下')


class GameRoundForm(FlaskForm):
    
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
    round = SelectField('选择投票轮次', choices=round_opts, validate_choice=False)
    

