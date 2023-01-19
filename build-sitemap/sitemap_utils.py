from xml.dom import minidom

def createSitemapFromList(urls, filename):
    doc = minidom.Document()
    root = doc.createElement("urlset")
    root.setAttribute("xmlns"  , "http://www.sitemaps.org/schemas/sitemap/0.9")
    root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.setAttribute("xsi:schemalocation"  , "http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd")
    doc.appendChild(root)

    for u in urls:
        element = doc.createElement("url")
        element2 = doc.createElement("loc")
        element2.appendChild(doc.createTextNode(u))
        element.appendChild(element2)
        root.appendChild(element)

    doc.appendChild(root)

    doc.writexml(open(filename,'w'),encoding='UTF-8')
