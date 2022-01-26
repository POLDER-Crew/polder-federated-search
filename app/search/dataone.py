from datetime import date
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
        logger.debug("dataone text search: %s", query)
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

    def date_filter_search(self, start_min=None, start_max=None, end_min=None, end_max=None):
        # some sensible defaults
        # convert it to a string representation of an ISO instant
        start_min = (start_min.isoformat() +
                     "Z" if start_min is not None else "*")

        start_max = (start_max.isoformat() +
                     "Z" if start_max is not None else "NOW")

        end_min = (end_min.isoformat() +
                     "Z" if end_min is not None else "*")

        end_max = (end_max.isoformat() +
                     "Z" if end_max is not None else "NOW")

        TIME_FILTER = f"(beginDate:[{start_min} TO {start_max}] OR endDate:[{end_min} TO {end_max}])"

        query = f"{self.ENDPOINT_URL}?fq=({self.LATITUDE_FILTER} AND {TIME_FILTER})&rows={self.PAGE_SIZE}&wt=json&fl=*,score"
        logger.debug("dataone temporal search: %s", query)
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
        urls = []
        dataUrl = result.pop('dataUrl', None)
        if dataUrl:
            urls.append(dataUrl)
        webUrl = result.pop('webUrl', [])
        if webUrl:
            urls.extend(webUrl)
        contentUrl = result.pop('contentUrl', None)
        if contentUrl:
            urls.extend(contentUrl['value'])

        doi = None
        if 'seriesId' in result and result['seriesId'].startswith('doi:'):
            doi = result['seriesId']

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
            doi=doi,
            keywords=result.pop('keywords', []),
            origin=result.pop('origin', []),
            # todo: temporal coverage
            urls=urls,
            source="DataONE"
        )
