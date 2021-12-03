import os
import logging
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

if __name__ == "__main__":
    # Only for debugging while developing
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=5000)
