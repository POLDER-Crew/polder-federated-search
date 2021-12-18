import json
import logging
import requests
from .search import SearcherBase, SearchResultSet, SearchResult

logger = logging.getLogger('app')


class SolrDirectSearch(SearcherBase):
    ENDPOINT_URL = "https://search.dataone.org/cn/v2/query/solr/"
    LATITUDE_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"

    def text_search(self, text=None):
        query = f"{self.ENDPOINT_URL}?q={text}&fq={self.LATITUDE_FILTER}&rows={self.PAGE_SIZE}&wt=json&fl=*,score"
        logger.debug("dataone query: %s", query)
        response = requests.get(query)
        response.raise_for_status()
        body = response.json()['response']
        self.max_score = body['maxScore']

        if self.max_score == 0:
            self.max_score = 0.00001

        result_set = SearchResultSet(
            total_results=body['numFound'],
            page_start=body['start'],
            results=self.convert_results(body['docs'])
        )

        return result_set

    def convert_result(self, result):
        return SearchResult(
                    # Because Blazegraph uses normalized query scores, we can approximate search
                    # ranking by normalizing these as well. However, this does nothing for the
                    # cases where the DataOne result set is more or less relevant, on average, than
                    # the one from Blazegraph / Gleaner.
                    score=(result.pop('score') / self.max_score),
                    title=result.pop('title', None),
                    id=result.pop('id', None),
                    abstract=result.pop('abstract', ""),
                    # todo: we can make a bounding box with eastBoundCoord, northBoundCoord,
                    # westBoundCoord and southBoundCoord in this data source
                    # But there is also a named place available, which is what is being used here
                    spatial_coverage=result.pop('placeKey', None),
                    # todo: temporal coverage
                    urls=result.pop('webUrl', []), # todo: not sure if webUrl is the right thing to use here
                    source="DataONE"
                )

