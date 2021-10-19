import unittest
import re
import requests
import requests_mock
from SPARQLWrapper import SPARQLExceptions
from urllib.parse import unquote

from app.search import dataone, gleaner

test_response = [{'some': 'result'}, {'another': 'result'}]

class TestSolrDirectSearch(unittest.TestCase):
    def setUp(self):
        self.search = dataone.SolrDirectSearch()

    @requests_mock.Mocker()
    def test_text_search(self, m):
        m.get(
            dataone.SolrDirectSearch.SOLR_ENDPOINT,
            json=test_response
        )
        results = self.search.text_search(q='test')
        self.assertEqual(results, test_response)

        # Did we make the query we expected?
        solr_url = m.request_history[0].url
        self.assertIn('?q=test', solr_url)

        # Did we add the latitude filter?
        self.assertIn(
            f'&fq={dataone.SolrDirectSearch.LATITUDE_FILTER}',
            unquote(solr_url)
        )

    @requests_mock.Mocker()
    def test_search_error(self, m):
        m.get(
            dataone.SolrDirectSearch.SOLR_ENDPOINT,
            status_code=500
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            results = self.search.text_search(q='test')

    def test_missing_kwargs(self):
        results = self.search.text_search()


class TestGleanerSearch(unittest.TestCase):
    def setUp(self):
        self.search = gleaner.GleanerSearch()

    @requests_mock.Mocker()
    def test_text_search(self, m):
        m.get(
            requests_mock.ANY,
            json=test_response
        )
        results = self.search.text_search(q='test')
        # self.assertIn(test_response, results)

    @unittest.skip("ugh")
    @requests_mock.Mocker()
    def test_search_error(self, m):
        m.get(
            gleaner.GleanerSearch.SPARQL_ENDPOINT,
            status_code=500
        )
        # with self.assertRaises(SPARQLExceptions.EndPointInternalError):
        results = self.search.text_search(q='test')

    @unittest.skip("bleh")
    def test_missing_kwargs(self):
        results = self.search.text_search()
