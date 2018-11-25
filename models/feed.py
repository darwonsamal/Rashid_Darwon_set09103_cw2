from mongoengine import CASCADE
from flask import url_for
import os
from flask_mongoengine import MongoEngine


from models.user import User
from utilities.common import linkify, ms_stamp_humanize, utc_now_ts_ms as now

STATIC_IMAGE_URL = '../static/images/posts/'

POST = 1
COMMENT = 2
LIKE = 3

messageType = (
    (POST, 'Post'),
    (COMMENT, 'Comment'),
    (LIKE, 'Like'),
)
    
from flask import current_app, Flask

app = Flask(__name__)

with app.app_context():

    db = MongoEngine(app)   

    class Message(db.Document):
        fromUser = db.ReferenceField(User, db_field="fu", reverse_delete_rule=CASCADE)
        toUser = db.ReferenceField(User, db_field="tu", default=None, reverse_delete_rule=CASCADE)
        text = db.StringField(db_field="t", max_length=1024)
        live = db.BooleanField(db_field="l", default=True)
        createDate = db.LongField(db_field="c", default=now())
        parent = db.ObjectIdField(db_field="p", default=None)
        image = db.StringField(db_field="i", default=None)
        messageType = db.IntField(db_field="mt", default=POST, choices=messageType)
         
            
        @property
        def comments(self):
            return Message.objects.filter(parent=self.id, messageType=COMMENT).order_by('createDate')

        @property
        def likes(self):
            return Message.objects.filter(parent=self.id, messageType=LIKE).order_by('-createDate')

        @property
        def linkifyText(self):
            return linkify(self.text)        
        
        @property
        def humanTimestamp(self):
            return ms_stamp_humanize(self.createDate)

        def post_imgsrc(self, size):

            if self.image:
               
                return self.image
            else:
                return 'no-post.%s.png'
        
    
        meta = {'indexes' : 
        [
            {
                'fields' : ['$text', '$createDate', '$fromUser', '$toUser'],
                'default_language': 'english',
                'weights' : {'text' : 10, 'createDate' : 8, 'fromUser' : 6, 'toUser' : 4}
            }
        ]}
        
    class Feed(db.Document):
        user = db.ReferenceField(User, db_field="u", reverse_delete_rule=CASCADE)
        message = db.ReferenceField(Message, db_field="m", reverse_delete_rule=CASCADE)
        createDate = db.LongField(db_field="c", default=now())

        meta = {
            'indexes': [('user', '-createDate')]
        }

    