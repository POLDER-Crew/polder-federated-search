import unittest
from unittest.mock import patch, mock_open, Mock
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

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_text_search(self, query):

        # Set up our mock SPARQLWrapper results. We have mocked out the query() method from
        # SPARQLWrapper, but that method returns an object that we immediately call convert() on,
        # and the results of that are what we work with.
        mock_convert = Mock(return_value={"results": {
            "bindings": [
                {
                    's': {'type': 'bnode', 'value': 'thing1'},
                    'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.01953125'},
                    'description': {'type': 'literal', 'value': "Here is a thing"},
                    'name': {'type': 'literal', 'value': 'thing'}
                },
                                {
                    's': {'type': 'bnode', 'value': 'thing2'},
                    'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.01953124'},
                    'description': {'type': 'literal', 'value': "Here is a less relevant thing"},
                    'name': {'type': 'literal', 'value': 'thing the second'}
                }
            ]
        }})
        mock_query = Mock()
        mock_query.convert = mock_convert
        query.return_value = mock_query

        # Do the actual test
        results = self.search.text_search(q='test')
        self.assertEqual(
            results,
            [{'s': 'thing1', 'score': '0.01953125', 'description': 'Here is a thing', 'name': 'thing'}, {'s': 'thing2', 'score': '0.01953124', 'description': 'Here is a less relevant thing', 'name': 'thing the second'}]
        )

    # gross, but requests-mock does not touch the requests
    # that SPARQLWrapper makes using good old urllib
    # for some reason, even if I try to capture
    # every request, so here we are creating fake file handles
    # because that's what the response object that
    # SPARQLWrapper knows how to work with expects
    @patch('SPARQLWrapper.Wrapper.urlopener')
    def test_search_error(self, urlopen):
        with patch("builtins.open", mock_open(read_data=test_response)) as file_patch:
            test_response_fp = open("foo")

        resp = addinfourl(
            test_response_fp, # our fake file pointer
            {}, # empty headers
            self.search.SPARQL_ENDPOINT
        )
        resp.code = 500
        urlopen.return_value = resp
        urlopen.side_effect = HTTPError(
            "oh no", 500, {}, {}, test_response_fp
        )
        with self.assertRaises(SPARQLExceptions.EndPointInternalError):
            results = self.search.text_search(q='test')
