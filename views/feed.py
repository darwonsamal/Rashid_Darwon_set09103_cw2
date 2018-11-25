from flask import Blueprint, request, session, redirect, url_for, abort, render_template
from werkzeug import secure_filename
import os
import uuid

from utilities.decorator import login_required
from models.user import User, Notification
from models.feed import Message, Feed, POST, COMMENT, LIKE
from models.relationship import Relationship

from forms.feed import FeedPostForm, PrivateMessageForm
from settings import UPLOAD_FOLDER

from utilities.common import utc_now_ts_ms as now

feed_app = Blueprint('feed_app', __name__)

@feed_app.route('/message/add', methods=['GET', 'POST'])
@login_required
def add_message():
    ref = request.referrer
    form = FeedPostForm()

    formModalMessage = PrivateMessageForm()
    
    if form.validate_on_submit():

        fromUser = User.objects.get(username=session.get('username'))
        fetchNotifications(fromUser)
        toUser = User.objects.get(username=request.values.get('toUser'))
      
        image = None 
    
        if request.files.get('image'):
            filename = secure_filename(form.image.data.filename)
            file_path = "images/posts/" + str(uuid.uuid4())  + filename 
            file_pathB = "static" + file_path
            form.image.data.save(file_pathB)
            image = str(file_path)
            print(image)
            print("Image gotten")

        print("AfterImage")
        print(image)
        post = form.post.data

        if toUser == fromUser:
            toUser = None
       
        message = Message(
            fromUser=fromUser,
            toUser=toUser,
            text=post,
            messageType=POST,
            ).save()
            
        
        feed = Feed(
            user=fromUser,
            message=message
            ).save()
            
       
        if image:         
            message.image = image
            message.save()
             
        
        process_message(message)
        
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('home_app.home'))
            
    else:
        return 'Error!'


@feed_app.route('/delete_post/<post_id>')
def delete_post(post_id):
    message = None 

    ref = request.referrer

    message = Message.objects.filter(id = post_id).first()

    if message.fromUser != session['username']:
        message.delete()

        if ref:

            return redirect(ref)
        else:
            return redirect(url_for('home_app.home'))

    else:

        if ref:
            return redirect(ref)
        else:
            
            return redirect(url_for('home_app.home'))


@feed_app.route('/message/<message_id>', methods=['GET', 'POST'])
def message(message_id, feed_id=None):
    form = FeedPostForm()
    message = None

    formModalMessage = PrivateMessageForm()
    
    message = Message.objects.filter(id=message_id).first()
    if not message:
        abort(404) 
    
    if message and message.parent:
        abort(404)

    if form.validate_on_submit() and session.get('username'):
      
        fromUser = User.objects.get(username=session.get('username'))
        fetchNotifications(fromUser)
        post = form.post.data
        
     
        comment = Message(
            fromUser=fromUser,
            text=post,
            messageType=COMMENT,
            parent=message_id
            ).save()
            
        return redirect(url_for('feed_app.message', message_id=message.id))
            
    return render_template('feed/message.html', 
        message=message,
        form=form,
        formModalMessage = formModalMessage
        )
        
@feed_app.route('/like/<message_id>', methods=('GET', 'POST'))
@login_required
def like_message(message_id):
    message = None
    formModalMessage = PrivateMessageForm()

    message = Message.objects.filter(id=message_id).first()
    if not message:
        abort(404)
    
    if message and message.parent:
        abort(404)
        
    fromUser = User.objects.get(username=session.get('username'))
    fetchNotifications(fromUser)
    
   
    existing_like = Message.objects.filter(
        parent=message_id,
        fromUser=fromUser).count()

    if not existing_like:
      
        like = Message(
            fromUser=fromUser,
            toUser=message.fromUser,
            messageType=LIKE,
            parent=message_id
            ).save()
        
    return redirect(url_for('feed_app.message', message_id=message.id))


def process_message(message):
    
    
    fromUser = message.fromUser
    friends = Relationship.objects.filter(
        fromUser=fromUser,
        rel_type=Relationship.FRIENDS,
        status=Relationship.APPROVED
    )

    for friend in friends:
        
        rel = Relationship.get_relationship(friend.toUser, message.toUser)
        if rel != "BLOCKED":
            feed = Feed(
                user=friend.toUser,
                message=message
            ).save()
    
    return True



def fetchNotifications(logged_user):

    notifications = Notification.objects.filter(toUser = logged_user.username)

    nlist = []

    for x in notifications:
        nlist.append(x)

    session['notifications'] = nlist