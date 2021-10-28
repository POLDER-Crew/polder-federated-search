import os

from flask import Flask

# create and configure the app
app = Flask(__name__, instance_relative_config=True)

# Because we have so many different kinds of deployments available,
# we're using environment variables for some of the config here.


# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

from app import routes
