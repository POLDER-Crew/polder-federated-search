import os
import logging
from flask import Flask
from flask_cachebuster import CacheBuster

# create and configure the app
app = Flask(__name__)

app.config.from_pyfile('app_config.cfg')

# Set up cache busting
cache_buster = CacheBuster(config=app.config['CACHE_BUSTER_CONFIG'])
cache_buster.init_app(app)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

from app import routes, template_helpers

if __name__ == "__main__":
    # Only for debugging while developing
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=5000)
