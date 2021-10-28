import os
from flask import Flask

# create and configure the app
app = Flask(__name__)

app.config.from_pyfile('app_config.cfg')

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

from app import routes
