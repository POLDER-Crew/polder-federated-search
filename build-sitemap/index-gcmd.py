from urllib.request import urlopen
from xml.dom import minidom
from sitemap_utils import createSitemapFromList

query = 'https://cmr.earthdata.nasa.gov/search/collections?data_center=AU/AADC&data_center=WGMS&data_center=DOC/NOAA/NESDIS/NCEI&data_center=ASF&data_center=NASA%20NSIDC%20DAAC&data_center=NO/NMDC/IMR&data_center=UK/NERC/POL/PSMSL&data_center=WDC/GEOMAGNETISM,%20EDINBURGH&data_center=WDC/SEP,%20MOSCOWIS/NCEI&data_center=NASA%20NSIDC%20DAAC&page_num={page:d}&page_size=2000'

def getData(item):
    return item.firstChild.data

# get the first page and info about following pages
baseurl = query.format(page=1)
mybasedoc = minidom.parse(urlopen(baseurl))
hits = mybasedoc.getElementsByTagName('hits')
pagecount = int(hits[0].firstChild.nodeValue)
amount_of_pages = int (pagecount/2000) + 2

# data on page 1
items = list(map(getData, mybasedoc.getElementsByTagName('location')))


# data from page 2 onwards
for i in range(2,amount_of_pages):
    url = query.format(page=i)
    mydoc = minidom.parse(urlopen(url))
    items.extend(list(map(getData, mydoc.getElementsByTagName('location'))))

createSitemapFromList(items,'gcmd-sitemap.xml')
