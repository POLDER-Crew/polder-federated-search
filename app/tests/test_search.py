import unittest
from unittest.mock import patch, mock_open
import re
import requests
import requests_mock
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError
from urllib.parse import unquote
from urllib.response import addinfourl

from app.search import dataone, gleaner

test_response = "[{'some': 'result'}, {'another': 'result'}]"

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

        # gross, but requests-mock does not touch the requests
        # that SPARQLWrapper makes using good old urllib
        # for some reason, even if I try to capture
        # every request, so here we are creating fake file handles
        # because that's what the response object that
        # SPARQLWrapper knows how to work with expects
        with patch("builtins.open", mock_open(read_data=test_response)) as file_patch:
            self.test_response_fp = open("foo")


    @patch('SPARQLWrapper.Wrapper.urlopener')
    def test_text_search(self, urlopen):
        urlopen.return_value = addinfourl(
            self.test_response_fp, # our fake file pointer
            {}, # empty headers
            self.search.SPARQL_ENDPOINT
        )
        results = self.search.text_search(q='test')
        self.assertIn(test_response, results)

    @patch('SPARQLWrapper.Wrapper.urlopener')
    def test_search_error(self, urlopen):
        resp = addinfourl(
            self.test_response_fp, # our fake file pointer
            {}, # empty headers
            self.search.SPARQL_ENDPOINT
        )
        resp.code = 500
        urlopen.return_value = resp
        urlopen.side_effect = HTTPError(
            "oh no", 500, {}, {}, self.test_response_fp
        )
        with self.assertRaises(SPARQLExceptions.EndPointInternalError):
            results = self.search.text_search(q='test')
