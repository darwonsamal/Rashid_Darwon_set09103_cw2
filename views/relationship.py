from flask import Blueprint, abort, session, redirect, url_for, request, render_template

from models.user import User, Notification
from models.relationship import Relationship
from utilities.decorator import login_required
from utilities.common import email

from settings import WEBSITE_ADDRESS

relationship_app = Blueprint('relationship_app', __name__)




@relationship_app.route('/add_friend/<to_username>')
@login_required
def add_friend(to_username):

    ref = request.referrer
    logged_user = User.objects.filter(username=session.get('username')).first()
    fetchNotifications(logged_user)
    
    toUser = User.objects.filter(username=to_username).first()

    if toUser:

        rel = Relationship.get_relationship(logged_user, toUser)
        to_username = toUser.username

        if rel == "REVERSE_FRIENDS_PENDING":
           
            Relationship(
                fromUser=logged_user, 
                toUser=toUser,
                rel_type=Relationship.FRIENDS,
                status=Relationship.APPROVED
                ).save()
            reverse_rel = Relationship.objects.get(
                fromUser=toUser,
                toUser=logged_user)
            reverse_rel.status=Relationship.APPROVED
            reverse_rel.save()

            notification = Notification.objects.filter(fromUser = toUser.username, toUser = logged_user.username ).first()

            if notification != None:

                nlist = session.get('notifications')

                nlist.remove(notification)

                session['notifications'] = nlist

                notification.delete()

            

        elif rel == None and rel != "REVERSE_BLOCKED":
           
            Relationship(
                fromUser=logged_user, 
                toUser=toUser, 
                rel_type=Relationship.FRIENDS, 
                status=Relationship.PENDING
                ).save()
                
           
            body_html = render_template('mail/relationship/added_friend.html', fromUser=logged_user, toUser=toUser, host = WEBSITE_ADDRESS)
            body_text = render_template('mail/relationship/added_friend.txt', fromUser=logged_user, toUser=toUser, host = WEBSITE_ADDRESS)
            email(toUser.email, ("%s has requested to be friends") % logged_user.first_name, body_html, body_text)


            notification = Notification(fromUser = logged_user.username, toUser = toUser.username, notificationType = "request")

            notification.save()

            
          

        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', username=toUser.username))
    else:
        abort(404)
        
@relationship_app.route('/remove_friend/<to_username>')
@login_required
def remove_friend(to_username):
    ref = request.referrer
    logged_user = User.objects.filter(username=session.get('username')).first()
    fetchNotifications(logged_user)
   
    toUser = User.objects.filter(username=to_username).first()
    if toUser:
        rel = Relationship.get_relationship(logged_user, toUser)
        if rel == "FRIENDS_PENDING" or rel == "FRIENDS_APPROVED" or rel == "REVERSE_FRIENDS_PENDING":
            rel = Relationship.objects.filter(
                fromUser=logged_user,
                toUser=toUser).delete()
            reverse_rel = Relationship.objects.filter(
                fromUser=toUser,
                toUser=logged_user).delete()
            
            notification = Notification.objects.filter(fromUser = toUser.username, toUser = logged_user.username ).first()

            if notification != None:

                nlist = session.get('notifications')

                nlist.remove(notification)

                session['notifications'] = nlist

                notification.delete()
            
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', username=toUser.username))
    else:
        abort(404)
        
@relationship_app.route('/block/<to_username>')
@login_required
def block(to_username):
    ref = request.referrer
    logged_user = User.objects.filter(username=session.get('username')).first()
    fetchNotifications(logged_user)
    toUser = User.objects.filter(username=to_username).first()
    if toUser:
        rel = Relationship.get_relationship(logged_user, toUser)
        if rel == "FRIENDS_PENDING" or rel == "FRIENDS_APPROVED" or rel == "REVERSE_FRIENDS_PENDING":
            rel = Relationship.objects.filter(
                fromUser=logged_user,
                toUser=toUser).delete()
            reverse_rel = Relationship.objects.filter(
                fromUser=toUser,
                toUser=logged_user).delete()
        Relationship(
            fromUser=logged_user, 
            toUser=toUser, 
            rel_type=Relationship.BLOCKED, 
            status=Relationship.APPROVED
            ).save()
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', username=toUser.username))
    else:
        abort(404)
        
@relationship_app.route('/unblock/<toUsername>')
@login_required
def unblock(toUsername):
    ref = request.referrer
    logged_user = User.objects.filter(username=session.get('username')).first()

    fetchNotifications(logged_user)
    toUser = User.objects.filter(username=toUsername).first()
    if toUser:
        rel = Relationship.get_relationship(logged_user, toUser)
        if rel == "BLOCKED":
            rel = Relationship.objects.filter(
                fromUser=logged_user,
                toUser=toUser).delete()
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', username=toUser.username))
    else:
        abort(404)


def fetchNotifications(logged_user):

    notifications = Notification.objects.filter(toUser = logged_user.username)

    nlist = []

    for x in notifications:
        nlist.append(x)

    session['notifications'] = nlist