from urllib.request import urlopen
from xml.dom import minidom
import xml.etree.cElementTree as ET


root = ET.Element('root')
for i in range(1,8):
    url = 'https://cmr.earthdata.nasa.gov/search/collections?data_center=AU/AADC&data_center=WGMS&data_center=DOC/NOAA/NESDhttps://cmr.earthdata.nasa.gov/search/collections?data_center=AU/AADC&data_center=WGMS&data_center=DOC/NOAA/NESDIS/NCEI&data_center=ASF&data_center=NASA%20NSIDC%20DAAC&data_center=NO/NMDC/IMR&data_center=UK/NERC/POL/PSMSL&data_center=WDC/GEOMAGNETISM,%20EDINBURGH&data_center=WDC/SEP,%20MOSCOWIS/NCEI&data_center=NASA%20NSIDC%20DAAC&page_num='+str(i)+'&page_size=2000'
    mydoc = minidom.parse(urlopen(url))
    items = mydoc.getElementsByTagName('location')
    for i in items:
    	element = i.firstChild.data
    	print(element)
    	ET.SubElement(root,'location').text = element



tree = ET.ElementTree(root)
tree.write('gcmd-sitemap.xml')

