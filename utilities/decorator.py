
from flask import current_app, Flask, session, request, redirect, url_for

from functools import wraps
from models.feed import Message, Feed
from models.relationship import Relationship



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect(url_for('user_app.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function