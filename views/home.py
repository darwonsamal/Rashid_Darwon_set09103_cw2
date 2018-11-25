from flask import Blueprint, session, render_template

from models.user import User, Notification
from models.feed import Feed
from forms.feed import FeedPostForm, PrivateMessageForm

home_app = Blueprint('home_app', __name__)


@home_app.route('/')
def home(page = 1):  
    if session.get('username'):

        notificationsList = []

        formModalMessage = PrivateMessageForm()

        form = FeedPostForm()
        
        user = User.objects.filter(
            username=session.get('username')
            ).first()
        
        # get user messages

        feed_messages = Feed.objects.filter(user = user).order_by('-createDate')

        page = int(page)

        feed_messages = feed_messages.paginate(page = page, per_page = 5)

        for x in feed_messages.items:
            print(x.message.image)
  
        notifications = Notification.objects.filter(toUser = user.username)
        
        if notifications != None:

            for x in notifications:
                
                notificationsList.append(x)


        session['notifications'] = notificationsList

        return render_template('home/feed_home.html',
            user=user,
            form=form,
            feed_messages=feed_messages,
            formModalMessage = formModalMessage       
        )
        
    else:
        return render_template('home/home.html')


@home_app.route('/feed/<page>', methods = ['GET'])
def feedPage(page = 1):

    if session.get('username'):

        notificationsList = []

        formModalMessage = PrivateMessageForm()

        form = FeedPostForm()
        
        user = User.objects.filter(
            username=session.get('username')
            ).first()
        
        # get user messages

        feed_messages = Feed.objects.filter(user = user).order_by('-createDate')

        page = int(page)

        feed_messages = feed_messages.paginate(page = page, per_page = 5)

    
        notifications = Notification.objects.filter(toUser = user.username)
        
        if notifications != None:

            for x in notifications:
                
                notificationsList.append(x)


        session['notifications'] = notificationsList

        return render_template('home/feed_home.html',
            user=user,
            form=form,
            feed_messages=feed_messages,
            formModalMessage = formModalMessage)
    