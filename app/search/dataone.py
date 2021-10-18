from d1_client import solr_client
import requests
from .searcher_base import SearcherBase

# This may not get used, depending on the dataone python library status.
class DataOneSearch(SearcherBase):
    # https://dataone-python.readthedocs.io/en/latest/d1_client/api/d1_client.html#module-d1_client.solr_client
    client = solr_client.SolrClient()

    def text_search(self, **kwargs):
        return self.client.search(**kwargs)

class SolrDirectSearch(SearcherBase):
    SOLR_ENDPOINT = "https://search.dataone.org/cn/v2/query/solr/"
    LATLON_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"

    def text_search(self, **kwargs):
        response = requests.get(
            f"{self.SOLR_ENDPOINT}?q={kwargs['q']}&fq={self.LATLON_FILTER}&wt=json"
        )
        return response.json()
