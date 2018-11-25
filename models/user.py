from mongoengine import signals, CASCADE
import os
from flask_mongoengine import MongoEngine


from utilities import common

from utilities.common import *


from flask import current_app, Flask, url_for



STATIC_IMAGE_URL = "..\\static\\images\\user\\"

app = Flask(__name__)

with app.app_context():

    db = MongoEngine(app)

    class User(db.Document):
        username = db.StringField(db_field="u", required=True, unique=True)
        password = db.StringField(db_field="p", required=True)
        email = db.EmailField(db_field="e", required=True, unique=True)
        first_name = db.StringField(db_field="fn", max_length=50)
        last_name = db.StringField(db_field="ln", max_length=50)
        bio = db.StringField(db_field="bio", max_length=160)
        created = db.IntField(db_field="c", default= utc_now_ts())
        email_confirmed = db.BooleanField(db_field="ecf", default=False)
        change_configuration = db.DictField(db_field="cc")
        profile_image = db.StringField(db_field="i", default=None)
          

        @classmethod
        def pre_save(cls, sender, document, **kwargs):
            document.username = document.username.lower()
            document.email = document.email.lower()
            
        def profile_imgsrc(self, size):
            if self.profile_image:

                print(self.profile_image)
               
                return self.profile_image
            else:
                return "static/images/user/no-profile." + size + ".png"

        
            
        meta = {'indexes': 
            [
                {'fields': ['$username', '$first_name', '$last_name'],
                'default_language': 'english',
                'weights': {'username': 10, 'first_name' : 5, 'last_name' : 4}
                }]}
        
    signals.pre_save.connect(User.pre_save, sender=User)



    class PrivateMessage(db.Document):
        fromUser = db.ReferenceField(User, db_field="fu", reverse_delete_rule=CASCADE)
        toUser = db.ReferenceField(User, db_field="tu", default=None, reverse_delete_rule=CASCADE)
        createDate = db.StringField(db_field="c", default = str(utc_now_ts_ms()))
        text = db.StringField(db_field="t", max_length=1024)

        @property
        def linkifyText(self):
            return linkify(self.text)        
            
        @property
        def humanTimestamp(self):
            return ms_stamp_humanize(self.createDate)


        meta = {'indexes' : 
        [
            {
                'fields' : ['$text', '$createDate', '$fromUser', '$toUser'],
                'default_language': 'english',
                'weights' : {'text' : 10, 'createDate' : 8, 'fromUser' : 6, 'toUser' : 4}
            }
        ]}

    class Notification(db.Document):
        toUser =  db.StringField(db_field="tu", required = True )
        fromUser = db.StringField(db_field="fu", required = True)
        notificationType = db.StringField(db_field="nt", default = "request")


        meta = {'indexes' : 
        [
            {
                'fields' : ['$fromUser', '$notificationType', '$toUser'],
                'default_language': 'english',
                'weights' : {'fromUser' : 10, 'notificationType' : 8, 'toUser' : 8}
            }
        ]}
     