from urllib.request import urlopen
from xml.dom import minidom
import xml.etree.ElementTree as ET
from app import cache




#caching all the dataone original sources in memory (only update the datasources after 120 secs)
@cache.cached(timeout=120, key_prefix='cache_original sources for dataone')
def get_original_dataone_sources():
    datasources = dict()
    # XML SCRAPING
    mydoc = minidom.parse(urlopen("https://cn.dataone.org/cn/v2/node/"))
    tree = ET.parse(urlopen("https://cn.dataone.org/cn/v2/node/"))


    
    root = tree.getroot()
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



