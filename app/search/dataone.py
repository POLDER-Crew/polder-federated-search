from datetime import datetime, time
from urllib.parse import quote
import json
import logging
import math
from pygeojson import Point
import requests
from .search import SearcherBase, SearchResultSet, SearchResult
from app import app
from app import helper


logger = logging.getLogger('app')


class SolrDirectSearch(SearcherBase):
    ENDPOINT_URL = "https://search.dataone.org/cn/v2/query/solr/"
    LATITUDE_FILTER = "(northBoundCoord:[50 TO *] OR southBoundCoord:[* TO -50])"
    DUPLICATE_FILTER = " AND -obsoletedBy:*"
    LANDING_URL_PREFIX = "https://search.dataone.org/view/"
    KEYWORDS_BOOST = '5.0'
    ABSTRACT_BOOST = '2.0'
    TITLE_BOOST = '5.0'



    @staticmethod
    def build_query(user_query="", page_number=1):
        # NOTE: Page numbers start counting from 1, because this number gets exposed
        # to the user, and people who are not programmers are weirded out by 0-indexed things.
        # The max is there in case a negative url parameter gets in here and causes havoc.
        page_start = max(0, page_number - 1) * SolrDirectSearch.PAGE_SIZE
        return f"{SolrDirectSearch.ENDPOINT_URL}?start={page_start}&fq={SolrDirectSearch.LATITUDE_FILTER}{SolrDirectSearch.DUPLICATE_FILTER}{user_query}&defType=dismax&qf=keywords^{SolrDirectSearch.KEYWORDS_BOOST}+abstract^{SolrDirectSearch.ABSTRACT_BOOST}+title^{SolrDirectSearch.TITLE_BOOST}&rows={SolrDirectSearch.PAGE_SIZE}&wt=json&fl=*,score"

    @staticmethod
    def _build_text_search_query(text=None):
        if text:
            return f"&q={quote(text)}"
        else:
            return ""


    @staticmethod
    def _build_author_filter_query(author=None):
        if author:
            return f"&q=originText:"+author
        else:
            return ""



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

    def execute_query(self, query, page_number):
        response = requests.get(query)
        response.raise_for_status()
        body = response.json()['response']

        result_set = SearchResultSet(
            total_results=body['numFound'],
            page_number=page_number,
            available_pages=math.ceil(
                body['numFound'] / SolrDirectSearch.PAGE_SIZE),
            results=self.convert_results(body['docs'])
        )

        return result_set

    def text_search(self, **kwargs):
        text = kwargs.pop('text', None)
        if text!=None:
            #Remove all quotes ()
            text = text.replace("'",'')
            text = text.replace('"','')
        page_number = kwargs.pop('page_number', 0)

        query = SolrDirectSearch.build_query(
            self._build_text_search_query(text), page_number)
        logger.debug("dataone text search: %s", query)
        return self.execute_query(query, page_number)

    def date_filter_search(self, **kwargs):
        start_min = kwargs.pop('start_min', None)
        start_max = kwargs.pop('start_max', None)
        end_min = kwargs.pop('end_min', None)
        end_max = kwargs.pop('end_max', None)
        page_number = kwargs.pop('page_number', 0)

        query = SolrDirectSearch.build_query(
            self._build_date_filter_query(
                start_min, start_max, end_min, end_max),
            page_number
        )
        logger.debug("dataone temporal search: %s", query)
        return self.execute_query(query, page_number)

    def combined_search(self, **kwargs):
        text = kwargs.pop('text', None)
        if text!=None:
            #Remove all quotes ()
            text = text.replace("'",'')
            text = text.replace('"','')

        start_min = kwargs.pop('start_min', None)
        start_max = kwargs.pop('start_max', None)
        end_min = kwargs.pop('end_min', None)
        end_max = kwargs.pop('end_max', None)
        page_number = kwargs.pop('page_number', 0)
        author = kwargs.pop('author',None)
        query = self._build_text_search_query(text)
        query += self._build_author_filter_query(author)
        query += self._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        query = SolrDirectSearch.build_query(query, page_number)
        logger.debug("dataone combined search: %s", query)
        return self.execute_query(query, page_number)

    def convert_result(self, result):
        datasource = dict()
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

            # These values are shown in the UI; provide sensible defaults
            begin  = "Unknown"
            end = "Unknown"
            try:
                begin = datetime.date(datetime.fromisoformat(result.pop('beginDate').rstrip('Z'))).isoformat()
            except ValueError as ve:
                logger.error("Invalid start date in dataone result: %s %s", urls[0], ve)
            try:
                end = datetime.date(datetime.fromisoformat(result.pop('endDate').rstrip('Z'))).isoformat()
            except ValueError as ve:
                logger.error("Invalid end date in dataone result: %s %s", urls[0], ve)

            result['temporal_coverage'] = begin + "/" + end

        boundingbox = {'south': result.pop('southBoundCoord', None), 'north': result.pop(
            'northBoundCoord', None), 'west': result.pop('westBoundCoord', None), 'east': result.pop('eastBoundCoord', None)}

        if boundingbox:
            # Make a Point if the (north and south) and (east and west) have the same coordinates
            if boundingbox['north'] == boundingbox['south'] and boundingbox['east'] == boundingbox['west']:
                bbox = Point(coordinates=(boundingbox['east'], boundingbox['north'])
                                 )
            else:
                bbox = SearchResult.polygon_from_box(boundingbox)

        geometry = {
            # Named places, in DataONE results
            'text': result.pop('placeKey', None),
            'geometry_collection': bbox
        }
        # passing the dictionary with the original data sources
        self.data_source_key = result.pop('datasource', '').lstrip("urn:node:")
        if self.data_source_key in helper.get_original_dataone_sources():
            datasource = helper.get_original_dataone_sources()[
                self.data_source_key]

        # Assure that author is a list
        author = []
        author.append(result.pop('author', []))

        return SearchResult(
            score=result.pop('score'),
            title=result.pop('title', None),
            id=identifier,
            datasource=datasource,
            abstract=result.pop('abstract', ""),
            author=author,
            doi=doi,
            keywords=result.pop('keywords', []),
            origin=result.pop('origin', []),
            temporal_coverage=result.pop('temporal_coverage', ""),
            urls=urls,
            geometry=geometry,
            source="DataONE"
        )
