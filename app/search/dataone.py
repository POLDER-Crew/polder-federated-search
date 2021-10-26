import json
import requests
from .search import SearcherBase, SearchResultSet


class SolrDirectSearch(SearcherBase):
    ENDPOINT_URL = "https://search.dataone.org/cn/v2/query/solr/"
    LATITUDE_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"

    def text_search(self, **kwargs):
        text = kwargs.pop('q', '')
        response = requests.get(
            f"{self.ENDPOINT_URL}?q={text}&fq={self.LATITUDE_FILTER}&rows={self.PAGE_SIZE}&wt=json&fl=*,score"
        )
        response.raise_for_status()
        body = response.json()['response']

        result_set = SearchResultSet(
            total_results=body['numFound'],
            page_start=body['start'],
            results=body['docs']
        )
        return result_set
