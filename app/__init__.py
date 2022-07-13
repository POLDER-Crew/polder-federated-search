import logging
import os
import sentry_sdk
from flask import Flask
from flask_cachebuster import CacheBuster
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_caching import Cache
from urllib.request import urlopen
from xml.dom import minidom
import xml.etree.ElementTree as ET

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

from app import routes, template_helpers

#caching all the dataone original sources in memory (only update the datasources after 120 secs)
@cache.cached(timeout=120, key_prefix='cache_original sources for dataone')
def get_original_dataone_sources():
    datasources = dict()
    # XML SCRAPING
    mydoc = minidom.parse(urlopen("https://cn.dataone.org/cn/v2/node/"))
    tree = ET.parse(urlopen("https://cn.dataone.org/cn/v2/node/"))


    #node = mydoc.getElementsByTagName('node')
    root = tree.getroot()
    print(len(root))
    for node in root:
        y = {'key': None, 'name': None, 'url': None, 'logo': None}
        for child in node:
            if child.tag == 'name':
                y['name'] = child.text
            if child.tag =='identifier':
                nodekey = child.text.lstrip("urn:node:")
                y['key'] = nodekey

        for x in node.iter('property'):
            if x.attrib['key'] == 'CN_info_url':
                y['url'] = x.text
            if x.attrib['key'] == 'CN_logo_url':
                y['logo'] = x.text


        datasources[nodekey] = y


    return datasources

#caching all the gleaner original sources in memory (only update the datasources after 120 secs)
@cache.cached(timeout=120, key_prefix='cache_original sources for gleaner')
def get_original_gleaner_sources():
    gleaner_datasources = {
        'GEM' : {'key':'GEM','name': 'Greenland Ecosystem Monitoring', 'url':'https://g-e-m.dk/','logo':'img/gem.jpg'},
        'BAS' : {'key':'BAS','name': 'British Antarctic Survey', 'url':'https://www.bas.ac.uk/','logo':'img/bas.png'},
        'CCHDO': {'key':'CCHDO','name': 'CLIVAR and Carbon Hydrographic Data Office', 'url':'https://cchdo.ucsd.edu/','logo':'img/logo_cchdo.svg'}
    }
    return gleaner_datasources


app.gleaner_datasources = get_original_gleaner_sources()
app.datasources = get_original_dataone_sources()

if __name__ == "__main__":
    # Only for debugging while developing
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=5000)

    

