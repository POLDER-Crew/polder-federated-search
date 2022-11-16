import requests
import json
import numpy as np
import pandas as pd
import datetime
from requests.structures import CaseInsensitiveDict

# Make a get request to get the latest player data from the FPL API
#link = "https://api.datastream.org/v1/odata/v4/Metadata?$top=1000"
link = "https://api.datastream.org/v1/odata/v4/Metadata?$top=10000&$filter=RegionId eq 'hub.atlantic' or RegionId eq 'hub.lakewinnipeg' or RegionId eq 'hub.mackenzie'"
api_key = '3SKMA34iPB7LLcnweqd3IC7MdGXZRTNr'
headers = CaseInsensitiveDict()
headers["x-api-key"] = api_key
response = requests.get(link, headers=headers)
data = response.json()



'''
with open('datastream.json','w') as f:
    json.dump(data['value'], f)
'''