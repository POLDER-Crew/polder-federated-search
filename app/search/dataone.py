from datetime import datetime, time
from urllib.parse import quote
import json
import logging
import requests
from .search import SearcherBase, SearchResultSet, SearchResult

logger = logging.getLogger('app')


class SolrDirectSearch(SearcherBase):
    ENDPOINT_URL = "https://search.dataone.org/cn/v2/query/solr/"
    LATITUDE_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"
    LANDING_URL_PREFIX = "https://search.dataone.org/view/"

    @staticmethod
    def build_query(user_query=""):
        return f"{SolrDirectSearch.ENDPOINT_URL}?fq={SolrDirectSearch.LATITUDE_FILTER}{user_query}&rows={SolrDirectSearch.PAGE_SIZE}&wt=json&fl=*,score"

    @staticmethod
    def _build_text_search_query(text=None):
        if text is None:
            return ""

        else:
            return f"&q={text}"

    @staticmethod
    def _build_date_filter_query(start_min=None, start_max=None, end_min=None, end_max=None):
        # convert our dates to the string representation of an ISO instant that Solr wants
        # See https://solr.apache.org/guide/6_6/working-with-dates.html
        start_min = (datetime.combine(start_min, time.min).isoformat() +
                     "Z" if start_min is not None else "*")

        start_max = (datetime.combine(start_max, time.max).isoformat() +
                     "Z" if start_max is not None else "NOW")

        end_min = (datetime.combine(end_min, time.min).isoformat() +
                   "Z" if end_min is not None else "*")

        end_max = (datetime.combine(end_max, time.max).isoformat() +
                   "Z" if end_max is not None else "NOW")

        return f"&fq=(beginDate:[{start_min} TO {start_max}] AND endDate:[{end_min} TO {end_max}])"

    def execute_query(self, query):
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

    def text_search(self, text=None):
        query = SolrDirectSearch.build_query(
            self._build_text_search_query(text))
        logger.debug("dataone text search: %s", query)
        return self.execute_query(query)

    def date_filter_search(self, start_min=None, start_max=None, end_min=None, end_max=None):
        query = SolrDirectSearch.build_query(
            self._build_date_filter_query(start_min, start_max, end_min, end_max))
        logger.debug("dataone temporal search: %s", query)
        return self.execute_query(query)

    def combined_search(self, text=None, start_min=None, start_max=None, end_min=None, end_max=None):
        query = self._build_text_search_query(text)
        query += self._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        query = SolrDirectSearch.build_query(query)
        logger.debug("dataone combined search: %s", query)
        return self.execute_query(query)

    def convert_result(self, result):
        urls = []
        identifier = result.pop('id', None)
        # The landing page for DataONE datasets is always here
        landingUrl = self.LANDING_URL_PREFIX + quote(identifier)
        urls.append(landingUrl)

        webUrl = result.pop('webUrl', [])
        if webUrl:
            urls.extend(webUrl)
        contentUrl = result.pop('contentUrl', None)
        if contentUrl:
            urls.extend(contentUrl['value'])

        doi = None
        if 'seriesId' in result and result['seriesId'].startswith('doi:'):
            doi = result['seriesId']

        if 'beginDate' in result and 'endDate' in result:
            # convert from dates as represented by Solr
            # See https://solr.apache.org/guide/6_6/working-with-dates.html

            begin = datetime.fromisoformat(result.pop('beginDate').rstrip('Z'))
            end = datetime.fromisoformat(result.pop('endDate').rstrip('Z'))
            result['temporal_coverage'] = datetime.date(begin).isoformat() + "/" + datetime.date(end).isoformat()

        return SearchResult(
            # Because Blazegraph uses normalized query scores, we can approximate search
            # ranking by normalizing these as well. However, this does nothing for the
            # cases where the DataOne result set is more or less relevant, on average, than
            # the one from Blazegraph / Gleaner.
            score=(result.pop('score') / self.max_score),
            title=result.pop('title', None),
            id=identifier,
            abstract=result.pop('abstract', ""),
            # todo: we can make a bounding box with eastBoundCoord, northBoundCoord,
            # westBoundCoord and southBoundCoord in this data source
            # But there is also a named place available, which is what is being used here
            spatial_coverage=result.pop('placeKey', None),
            doi=doi,
            keywords=result.pop('keywords', []),
            origin=result.pop('origin', []),
            temporal_coverage=result.pop('temporal_coverage', ""),
            urls=urls,
            source="DataONE"
        )
