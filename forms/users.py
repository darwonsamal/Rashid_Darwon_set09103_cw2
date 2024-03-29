from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField
from wtforms.widgets import TextArea
from wtforms.fields.html5 import EmailField
from wtforms.validators import ValidationError
from flask_wtf.file import FileField, FileAllowed
import re

from models import user
from models.user import User

class BaseUserForm(FlaskForm):
    first_name = StringField('First Name', [validators.DataRequired()])
    last_name = StringField('Last Name', [validators.DataRequired()])
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    username = StringField('Username', [
            validators.DataRequired(),
            validators.Length(min=4, max=25)
        ])
    bio = StringField('Bio', 
            widget=TextArea(),
            validators=[validators.Length(max=160)]
        )

class PasswordBaseForm(FlaskForm):
    password = PasswordField('New Password', [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords must match'),
            validators.Length(min=4, max=80)
        ])
    confirm = PasswordField('Repeat Password')

class RegisterForm(BaseUserForm, PasswordBaseForm):
    def validate_username(form, field):
        if User.objects.filter(username=field.data.lower()).first():
            raise ValidationError('Username already exists')
        if not re.match("^[a-zA-Z0-9_-]{4,25}$", field.data):
            raise ValidationError('Invalid username')
                
    def validate_email(form, field):
        if User.objects.filter(email=field.data.lower()).first():
            raise ValidationError('Email is already in use')
            
class LoginForm(FlaskForm):
    username = StringField('Username', [
            validators.DataRequired(),
            validators.Length(min=4, max=25)
        ])
    password = PasswordField('Password', [
            validators.DataRequired(),
            validators.Length(min=4, max=80)
        ])
        
class EditForm(BaseUserForm):
    image = FileField('Profile image', validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only JPEG, PNG and GIFs allowed')
        ])

class ForgotForm(FlaskForm):
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    
class PasswordResetForm(PasswordBaseForm):
    current_password = PasswordField('Current Password', [
        validators.DataRequired(),
        validators.Length(min=4, max=80)
    ])