import logging
from os import environ

logger = logging.getLogger('app')
# Set logs to be a little less verbose
logger.setLevel(environ.get('LOG_LEVEL', logging.WARNING))
