# Initialize flask app and get an instance of flask app object 

from flask import Flask
from pyshop.database import init_db
from pyshop.config import Config
import os
import pyshop.models


def create_app():
    # Start up instance application
    _app = Flask(__name__)
    # Import settings for config of Flask
    _app.config.from_object(Config)

    _app.secret_key = os.urandom(24)
    init_db(_app)

    return _app


app = create_app()
