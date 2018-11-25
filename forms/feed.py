from flask_wtf import FlaskForm
from wtforms import validators, StringField
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed

class FeedPostForm(FlaskForm):
    image = FileField('Profile image', validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'PNG'], 'Only JPEG, PNG and GIFs allowed')
        ])
    post = StringField('Post',

            widget=TextArea(),

            validators=[
                
                validators.DataRequired(),
                validators.Length(max=1024)
        ])

class PrivateMessageForm(FlaskForm):
    message = StringField('Message',

            widget=TextArea(),

            validators=[
                
                validators.DataRequired(), 
                validators.Length(max=1024)
        ])