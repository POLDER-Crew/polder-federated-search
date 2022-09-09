import logging
import os
import sentry_sdk
from flask import Flask
from flask_cachebuster import CacheBuster
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_caching import Cache


cache = Cache()

sentry_sdk.init(
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.2
)

# create and configure the app
app = Flask(__name__)

app.config.from_pyfile('app_config.cfg')
app.config['CACHE_TYPE'] = 'simple'
cache.init_app(app)

# Set up cache busting
cache_buster = CacheBuster(config=app.config['CACHE_BUSTER_CONFIG'])
cache_buster.init_app(app)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass


@app.context_processor
def inject_google_analytics_id():
    return dict(google_analytics_id=app.config['GOOGLE_ANALYTICS_ID'])

from app import routes, template_helpers


if __name__ == "__main__":
    # Only for debugging while developing
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=5000)
