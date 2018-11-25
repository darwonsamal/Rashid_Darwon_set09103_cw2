from flask import Blueprint, render_template, request, redirect, session, url_for, abort
from operator import itemgetter
from bcrypt import hashpw, checkpw, gensalt
import uuid
import os
from werkzeug import secure_filename
from mongoengine import Q

from models.user import User, PrivateMessage, Notification
from forms.users import RegisterForm, LoginForm, EditForm, ForgotForm, PasswordResetForm
from forms.feed import PrivateMessageForm
from utilities.common import email
from settings import UPLOAD_FOLDER, MAIL_USERNAME
from models.relationship import Relationship
from utilities.decorator import login_required
from forms.feed import FeedPostForm
from models.feed import Message, POST

import datetime 

now = datetime.datetime.now()

from settings import WEBSITE_ADDRESS

user_app = Blueprint('user_app', __name__)

@user_app.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    error = None

    formModalMessage = PrivateMessageForm()

    if request.method == 'GET' and request.args.get('next'):
        session['next'] = request.args.get('next', None)

    if form.validate_on_submit():
        user = User.objects.filter(
            username=form.username.data,
            ).first()
        if user:
            if user.password == hashpw(form.password.data.encode('UTF_8'), user.password.encode('UTF_8')).decode():

                session['username'] = form.username.data

                if 'next' in session:
                    next = session.get('next')
                    session.pop('next')
                    return redirect(next)
                else:
                    return redirect(url_for('home_app.home'))
            else:
                user = None
        if not user:
            error = "Incorrect credentials"
    return render_template('user/login.html', form=form, error=error, formModalMessage = formModalMessage)

@user_app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        salt = gensalt()
        hashed_password = hashpw(form.password.data.encode('utf8'), salt)
        code = str(uuid.uuid4())
        user = User(
            username=form.username.data,
            password=hashed_password,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            change_configuration={
                "new_email": form.email.data,
                "confirmation_code": code
                }
        )

        # email the user
        body_html = render_template('mail/user/register.html', user=user, host = WEBSITE_ADDRESS)
        body_text = render_template('mail/user/register.txt', user=user, host = WEBSITE_ADDRESS)
        email(user.email,  "Welcome to the social network", body_html, body_text)
        user.save()

        return redirect(url_for('user_app.login'))
    return render_template('user/register.html', form=form)

@user_app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('user_app.login'))

@user_app.route('/<username>/friends/<int:friends_page>', endpoint='profile-friends-page')
@user_app.route('/<username>/friends', endpoint='profile-friends')
@user_app.route('/<username>')
def profile(username, page=1, viewPage = 1):

    formModalMessage = PrivateMessageForm()

    logged_user = None
    rel = None
    friends_page = False
    user = User.objects.filter(username=username).first()
    profile_messages = []

    if user:
        if session.get('username'):
            logged_user = User.objects.filter(
                username=session.get('username')
                ).first()
            rel = Relationship.get_relationship(logged_user, user)
            fetchNotifications(logged_user)

        # get friends
        friends = Relationship.objects.filter(
            fromUser=user,
            rel_type=Relationship.FRIENDS,
            status=Relationship.APPROVED
            )
        friends_total = friends.count()

        if 'friends' in request.url:
            friends_page = True
            friends = friends.paginate(page=friends_page, per_page=8)
        else:
            friends = friends[:5]

        form = FeedPostForm()

        # get user messages if friends
        if logged_user and (rel == "SAME" or rel == "FRIENDS_APPROVED"):

            profile_messages = Message.objects.filter(
                Q(fromUser=user) | Q(toUser=user),
                messageType=POST,
                ).order_by('-create_date')

            viewPage = int(viewPage)

            print(viewPage)
            print(page)

            profile_messages = profile_messages.paginate(page = viewPage, per_page = 5)


        return render_template('user/profile.html',
            user=user,
            logged_user=logged_user,
            rel=rel,
            friends=friends,
            friends_total=friends_total,
            friends_page=friends_page,
            form=form,
            profile_messages=profile_messages,
            formModalMessage = formModalMessage
            )
    else:
        abort(404)


@user_app.route("/<username>/posts/<viewPage>")
def viewProfilePage(username, viewPage):

    return profile(username, 1, viewPage)


@user_app.route('/edit', methods=('GET', 'POST'))
@login_required
def edit():
    error = None
    message = None
    user = User.objects.filter(username=session.get('username')).first()

    formModalMessage = PrivateMessageForm()

    if user:
        form = EditForm(obj=user)

        fetchNotifications(user)

        if form.validate_on_submit():
            # check if image
            image_ts = None
            if request.files.get('image'):
                filename = secure_filename(form.image.data.filename)
                file_path = "static/images/user/" + str(user.id) + filename 
                form.image.data.save(file_path)
                image_ts = str(file_path)

                print(image_ts)

            # check if new username
            if user.username != form.username.data.lower():
                if User.objects.filter(username=form.username.data.lower()).first():
                    error = 'Username already exists'
                else:
                    session['username'] = form.username.data.lower()
                    form.username.data = form.username.data.lower()
            # check if new email
            if user.email != form.email.data.lower():
                if User.objects.filter(email=form.email.data.lower()).first():
                    error = 'Email already exists'
                else:
                    code = str(uuid.uuid4())
                    user.change_configuration = {
                        "new_email": form.email.data.lower(),
                        "confirmation_code": code
                        }
                    user.email_confirmed = False
                    form.email.data = user.email
                    message = "You will need to confirm the new email to complete this change"

                    # email the user
                    body_html = render_template('mail/user/change_email.html', user=user, host = WEBSITE_ADDRESS)
                    body_text = render_template('mail/user/change_email.txt', user=user, host = WEBSITE_ADDRESS)
                    email(user.change_configuration['new_email'], "Confirm your new email", body_html, body_text)

            if not error:

                form.populate_obj(user)

                if image_ts:
                    user.profile_image = image_ts
                    print("image_ts")
                    print(image_ts)
                user.save()

                if not message:
                    message = "Profile updated"

        return render_template('user/edit.html', form=form, error=error, message=message, user=user, formModalMessage = formModalMessage)
    else:
        abort(404)

@user_app.route('/confirm/<username>/<code>')
def confirm(username, code):

    edit_profile = False
    user = User.objects.filter(username=username).first()

    if user and user.change_configuration and user.change_configuration.get('confirmation_code'):
        if code == user.change_configuration.get('confirmation_code'):
            user.email = user.change_configuration.get('new_email')
            user.change_configuration = {}
            user.email_confirmed = True
            user.save()
            return render_template('user/email_confirmed.html')
    abort(404)

@user_app.route('/forgot', methods=('GET', 'POST'))
def forgot():
    error = None
    message = None
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.objects.filter(email=form.email.data).first()
        if user:
            code = str(uuid.uuid4())
            user.change_configuration={
                "password_reset_code": code
            }
            user.save()
            # email the user
            body_html = render_template('mail/user/password_reset.html', user=user, host = WEBSITE_ADDRESS)
            body_text = render_template('mail/user/password_reset.txt', user=user, host = WEBSITE_ADDRESS)
            email(user.email, "Password reset request", body_html, body_text)

        message = "You will receive a password reset email if we find that email in our system"
    return render_template('user/forgot.html', form=form, error=error, message=message)

@user_app.route('/password_reset/<username>/<code>', methods=('GET','POST'))
def password_reset(username, code):
    require_current = False

    form = PasswordResetForm()

    user = User.objects.filter(username=username).first()

    if not user or code != user.change_configuration.get('password_reset_code'):
        abort(404)

    if request.method == 'POST':
        del form.current_password
        if form.validate_on_submit():
            salt = gensalt()
            hashed_password = hashpw(form.password.data.encode('utf8'), salt).decode()
            user.password = hashed_password
            user.change_configuration = {}
            user.save()
            # if user is logged in, log him out
            if session.get('username'):
                session.pop('username')

            return redirect(url_for('user_app.password_reset_complete'))

    return render_template('user/password_reset.html',
        form=form,
        require_current=require_current,
        username=username,
        code=code
        )

@user_app.route('/password_reset_complete')
def password_reset_complete():
    return render_template('user/password_change_confirmed.html')

@user_app.route('/change_password', methods=('GET','POST'))
def change_password():

    require_current = True
    error = None
    form = PasswordResetForm()

    formModalMessage = PrivateMessageForm()

    user = User.objects.filter(username=session.get('username')).first()

    if not user:
        abort(404)

    if request.method == 'POST':
        if form.validate_on_submit():

            if user.password == hashpw(form.current_password.data.encode('utf8'), user.password.encode('utf8')).decode():

                salt = gensalt()
                hashed_password = hashpw(form.password.data.encode('utf8'), salt).decode()
                print(type(hashed_password))
                user.password = hashed_password
                user.save()
                # if user is logged in, log him out
                if session.get('username'):
                    session.pop('username')
                return redirect(url_for('user_app.password_reset_complete'))
            else:
                error = "Incorrect password"


    fetchNotifications(user)

    return render_template('user/password_reset.html',
        form=form,
        require_current=require_current,
        error=error,
        formModalMessage = formModalMessage
        )

@user_app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    form = PrivateMessageForm()

    ref = request.referrer

    if request.method == 'POST':


        if form.validate_on_submit():

            fromUser = User.objects.get(username=session.get('username'))
            fetchNotifications(fromUser)
            toUser = User.objects.get(username=request.values.get('toUser'))
            message = form.message.data

        
            message = PrivateMessage(
                fromUser = fromUser,
                toUser = toUser,
                text = message,
                createDate = str(now.strftime("%Y-%m-%d %H:%M"))

            ).save()

            
            form.message.data = ""

            notification = Notification(
                fromUser = fromUser.username, 
                toUser = toUser.username, 
                notificationType = "message")

            notification.save()

            return redirect(ref)

          

@user_app.route('/send_message_modal', methods = ['POST'])
@login_required
def send_message_modal():

    ref = request.referrer

    if request.method == 'POST':

            
            fromUser = User.objects.get(username=session.get('username'))

            fetchNotifications(fromUser)
            toUser = User.objects.get(username=request.values.get('toUser'))
            message = request.form['modalMessage']

        
            message = PrivateMessage(
                fromUser = fromUser,
                toUser = toUser,
                text = message,

            ).save()
     
           

            notification = Notification(
                fromUser = fromUser.username, 
                toUser = toUser.username, 
                notificationType = "message")

            notification.save()


            fetchNotifications(fromUser)

            notifications = Notification.objects.filter(fromUser = toUser.username, toUser = fromUser.username).first()

            if notifications != None:

                nlist = session.get('notifications')

                nlist.remove(notifications)

                session['notifications'] = nlist

                notifications.delete()


            return redirect(ref)


@user_app.route('/dismiss/<toUser>', methods=['GET'])
@login_required
def dismiss(toUser):

    ref = request.referrer

    if request.method == 'GET':
            
            fromUser = User.objects.get(username=session.get('username'))

            fetchNotifications(fromUser)
            toUser = User.objects.get(username=toUser)
        
            notifications = Notification.objects.filter(fromUser = toUser.username, toUser = fromUser.username).first()

            if notifications != None:

                nlist = session.get('notifications')

                nlist.remove(notifications)

                session['notifications'] = nlist

                notifications.delete()

            return redirect(ref)

    else:

        return redirect(ref)



@user_app.route('/private_message/<username>', methods=['GET'])
@user_app.route('/private_message/<username>/page/<viewPage>', methods= ['GET'])
def view_messages(username, viewPage = 1):

    form = PrivateMessageForm()
    formModalMessage = PrivateMessageForm()
    
    fromUser = User.objects.get(username=session.get('username'))
    toUser = User.objects.get(username = username)

    fetchNotifications(fromUser)

    privateMessagesList = PrivateMessage.objects.filter(Q(fromUser = fromUser, toUser = toUser) | Q(fromUser = toUser, toUser = fromUser)).order_by('createDate')


    if '/page' not in request.path:
        tempList = privateMessagesList.paginate(page = 1, per_page = 10)

        viewPage = tempList.pages

    viewPage = int(viewPage)

    if viewPage == 0:
        viewPage = 1
    

    print(viewPage)

    privateMessagesList = privateMessagesList.paginate(page = viewPage, per_page = 10)

    print(privateMessagesList.page)

    notification = Notification.objects.filter(fromUser = toUser.username, toUser = fromUser.username ).first()

    if notification != None:

        nlist = session.get('notifications')

        nlist.remove(notification)

        session['notifications'] = nlist

        notification.delete()

    return render_template('feed/private_message.html', 
        form = form, 
        user = fromUser, 
        toUser = toUser, 
        privateMessages = privateMessagesList, 
        formModalMessage = formModalMessage
    )

@user_app.route('/clearChat/<username>')
def clear_chat(username):

    fromUser = User.objects.get(username=session.get('username'))
    toUser = User.objects.get(username = username)

    fetchNotifications(fromUser)

    privateMessagesList = PrivateMessage.objects.filter(Q(fromUser = fromUser, toUser = toUser) | Q(fromUser = toUser, toUser = fromUser)).order_by('createDate')

    privateMessagesList.delete()





def sortList(privateMessages):
    tupleList = []

    for x in privateMessages:

        createDate = x.createDate
        messageID = x.id

        tupleList.append((messageID, createDate))

    tupleList = sorted(tupleList, key= itemgetter(1))

    sortedMessages = []
    for x in tupleList:

        for y in privateMessages:

            if x[0] == y.id:

                sortedMessages.append(y)

    return sortedMessages


def fetchPrivateMessages(fromUser, toUser):

    privateMessages = PrivateMessage.objects.filter(Q(fromUser = fromUser, toUser = toUser) | Q(fromUser = toUser, toUser = fromUser)).order_by('createDate')

    return privateMessages


def fetchNotifications(logged_user):

    notifications = Notification.objects.filter(toUser = logged_user.username)

    nlist = []

    for x in notifications:
        nlist.append(x)

    session['notifications'] = nlist
