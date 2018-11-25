from mongoengine import CASCADE
from flask_mongoengine import MongoEngine

from utilities.common import utc_now_ts as now
from models.user import User


from flask import current_app, Flask

app = Flask(__name__)

with app.app_context():

    db = MongoEngine(app)
    
    class Relationship(db.Document):
        
        FRIENDS = 1
        BLOCKED = -1

        RELATIONSHIP_TYPE = (
            (FRIENDS, 'Friends'),
            (BLOCKED, 'Blocked'),
        )
        
        PENDING = 0
        APPROVED = 1
        
        STATUS_TYPE = (
            (PENDING,  'Pending'),
            (APPROVED, 'Approved'),
        )
        
        fromUser = db.ReferenceField(User, db_field="fu", reverse_delete_rule=CASCADE)
        toUser = db.ReferenceField(User, db_field="tu", reverse_delete_rule=CASCADE)
        rel_type = db.IntField(db_field="rt", choices=RELATIONSHIP_TYPE)
        status = db.IntField(db_field="s", choices=STATUS_TYPE)
        req_date = db.IntField(db_field="rd", default=now())
        approved_date = db.IntField(db_field="ad", default=0)
        
        def is_friend(self, user):

            if user:
                return self.get_relationship(user, self.toUser)
            else:
                return None

        @staticmethod
        def get_relationship(fromUser, toUser):

            if fromUser == toUser:
                return 'SAME'

            rel = Relationship.objects.filter(
                fromUser=fromUser, 
                toUser=toUser
                ).first()

            if rel and rel.rel_type == Relationship.FRIENDS:

                if rel.status == Relationship.PENDING: 
                    return "FRIENDS_PENDING"

                if rel.status == Relationship.APPROVED:
                    return "FRIENDS_APPROVED"

            elif rel and rel.rel_type == Relationship.BLOCKED:
                return "BLOCKED"
                
            else:

                reverse_rel = Relationship.objects.filter(
                    fromUser=toUser,
                    toUser=fromUser,
                    ).first()

                if reverse_rel and reverse_rel.rel_type == Relationship.FRIENDS:

                    if reverse_rel.status == Relationship.PENDING: 
                        return "REVERSE_FRIENDS_PENDING"

                elif reverse_rel and reverse_rel.rel_type == Relationship.BLOCKED: 
                    return "REVERSE_BLOCKED"
                    
            return None

        meta = {
            'indexes': [('fromUser', 'toUser'), ('fromUser', 'toUser', 'rel_type', 'status')]
            }