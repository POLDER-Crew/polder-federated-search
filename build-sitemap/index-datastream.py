import requests
import json
from requests.structures import CaseInsensitiveDict
from sitemap_utils import createSitemapFromList

# Make a get request to get Metadata info from Datastream

link = "https://api.datastream.org/v1/odata/v4/Metadata?$top=10000&$filter=RegionId eq 'hub.atlantic' or RegionId eq 'hub.lakewinnipeg' or RegionId eq 'hub.mackenzie'"
api_key = '3SKMA34iPB7LLcnweqd3IC7MdGXZRTNr'
headers = CaseInsensitiveDict()
headers["x-api-key"] = api_key
response = requests.get(link, headers=headers)
data = response.json()['value']

dataUrls = map(lambda d: 'https://doi.org/' + d['DOI'], data)
createSitemapFromList(dataUrls, 'datastream-sitemap.xml')
