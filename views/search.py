from flask import Flask, Blueprint, render_template, request, redirect, session, url_for, abort

from models.user import User
from flask_mongoengine import *
from models.feed import Message


search_app = Blueprint('search_app', __name__)

app = Flask(__name__)


@search_app.route('/search', methods = ['POST'])
def search():

        if request.method == 'POST':

                #check if user searched for users

                search = request.form['search']

                users = User.objects.search_text(search)

                postList = []

                print(users)

                posts = Message.objects.search_text(search)


                return render_template('feed/search.html', users = users, posts = posts)
