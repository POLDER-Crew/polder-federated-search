import json
import requests
from .searcher_base import SearcherBase

class SolrDirectSearch(SearcherBase):
    SOLR_ENDPOINT = "https://search.dataone.org/cn/v2/query/solr/"
    LATITUDE_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"

    def text_search(self, **kwargs):
        text = kwargs.pop('q', '')
        response = requests.get(
            f"{self.SOLR_ENDPOINT}?q={text}&fq={self.LATITUDE_FILTER}&wt=json&fl=*,score"
        )
        response.raise_for_status()
        return response.json()['response']
