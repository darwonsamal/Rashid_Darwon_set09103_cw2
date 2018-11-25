import configparser
import codecs
from flask import *
import json
from datetime import *
from operator import itemgetter
from flask_mongoengine import MongoEngine
from flask_mail import *



import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


app = Flask(__name__)

    # Load config
app.config.from_pyfile('settings.py')

with app.app_context():
    db = MongoEngine(app)
    mail = Mail(app)
  
    

    

    
    # import blueprints
from views import users
from views.users import user_app
from views.relationship import relationship_app
from views.feed import feed_app
from views.home import home_app
from views.search import search_app

    # register blueprints
app.register_blueprint(user_app)
app.register_blueprint(relationship_app)
app.register_blueprint(feed_app)
app.register_blueprint(home_app)
app.register_blueprint(search_app)
    
    




if __name__ == '__main__':
    app.run( debug = True)
   