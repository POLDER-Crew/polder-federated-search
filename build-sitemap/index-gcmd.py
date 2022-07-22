from urllib.request import urlopen
from xml.dom import minidom

doc = minidom.Document()
root = doc.createElement("urlset")
root.setAttribute("xmlns"  , "http://www.sitemaps.org/schemas/sitemap/0.9")
root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
root.setAttribute("xsi:schemalocation"  , "http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd")

doc.appendChild(root)
query = 'https://cmr.earthdata.nasa.gov/search/collections?data_center=AU/AADC&data_center=WGMS&data_center=DOC/NOAA/NESDIS/NCEI&data_center=ASF&data_center=NASA%20NSIDC%20DAAC&data_center=NO/NMDC/IMR&data_center=UK/NERC/POL/PSMSL&data_center=WDC/GEOMAGNETISM,%20EDINBURGH&data_center=WDC/SEP,%20MOSCOWIS/NCEI&data_center=NASA%20NSIDC%20DAAC&page_num={page:d}&page_size=2000'

# data on page 1
baseurl = query.format(page=1)
mybasedoc = minidom.parse(urlopen(baseurl))
hits = mybasedoc.getElementsByTagName('hits')
items_page_1 = mybasedoc.getElementsByTagName('location')
for i in items_page_1:
        element = doc.createElement("url")
        element2 = doc.createElement("loc")
        element2.appendChild(doc.createTextNode(i.firstChild.data))
        element.appendChild(element2)
        root.appendChild(element)



pagecount = int(hits[0].firstChild.nodeValue)
amount_of_pages = int (pagecount/2000) + 2

# data from page 2 onwards
for i in range(2,amount_of_pages):
    url = query.format(page=i)
    mydoc = minidom.parse(urlopen(url))
    items = mydoc.getElementsByTagName('location')
    for i in items:
        element = doc.createElement("url")
        element2 = doc.createElement("loc")
        element2.appendChild(doc.createTextNode(i.firstChild.data))
        element.appendChild(element2)
        root.appendChild(element)



doc.writexml(open('gcmd-sitemap.xml','w'),encoding='UTF-8')
