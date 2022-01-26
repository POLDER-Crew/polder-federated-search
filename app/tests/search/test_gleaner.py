import unittest
from unittest.mock import patch, mock_open, Mock
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError
from urllib.response import addinfourl
from app.search import gleaner, search

class TestGleanerSearch(unittest.TestCase):
    def setUp(self):
        self.search = gleaner.GleanerSearch(endpoint_url="http://test")

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_text_search(self, query):

        # Set up our mock SPARQLWrapper results. We have mocked out the query() method from
        # SPARQLWrapper, but that method returns an object that we immediately call convert() on,
        # and the results of that are what we work with.
        result1 = {
            's': {'type': 'bnode', 'value': 'thing1'},
            'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.01953125'},
            'abstract': {'type': 'literal', 'value': "Here is a thing"},
            'title': {'type': 'literal', 'value': 'thing'},
            'id': {'type': 'literal', 'value': 'urn:uuid:asdfasdfasdf'}
        }
        result2 = {
            's': {'type': 'bnode', 'value': 'thing2'},
            'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.01953124'},
            'abstract': {'type': 'literal', 'value': "Here is a less relevant thing"},
            'title': {'type': 'literal', 'value': 'thing the second'},
            'id': {'type': 'literal', 'value': 'urn:uuid:some long thing'}

        }
        mock_convert = Mock(return_value={"results": {
            "bindings": [result1, result2]
        }})
        mock_query = Mock()
        mock_query.convert = mock_convert
        query.return_value = mock_query

        # Do the actual test
        expected = search.SearchResultSet(
            total_results=2,
            page_start=0,
            results=[
                self.search.convert_result(result1),
                self.search.convert_result(result2)
            ]

        )
        results = self.search.text_search('test')
        self.assertEqual(results, expected)

    # gross, but requests-mock does not touch the requests
    # that SPARQLWrapper makes using good old urllib
    # for some reason, even if I try to capture
    # every request, so here we are creating fake file handles
    # because that's what the response object that
    # SPARQLWrapper knows how to work with expects
    @patch('SPARQLWrapper.Wrapper.urlopener')
    def test_search_error(self, urlopen):
        with patch("builtins.open", mock_open(read_data="some data")) as file_patch:
            test_response_fp = open("foo")

        resp = addinfourl(
            test_response_fp,  # our fake file pointer
            {},  # empty headers
            self.search.ENDPOINT_URL
        )
        resp.code = 500
        urlopen.return_value = resp
        urlopen.side_effect = HTTPError(
            "oh no", 500, {}, {}, test_response_fp
        )
        with self.assertRaises(SPARQLExceptions.EndPointInternalError):
            results = self.search.text_search('test')

    def test_convert_result(self):
        test_result = {
            'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.375'},
            'abstract': {'type': 'literal', 'value': 'This data file contains information'},
            'title': {'type': 'literal', 'value': 'Iceflux trawl (SUIT & RMT) and ice stations'},
            'url': {'type': 'literal', 'value': 'url1'},
            'sameAs': {'type': 'literal', 'value': 'url2'},
            'spatial_coverage': {'type': 'literal', 'value': '-70.5397 -10.4515 -57.4443 0.018'},
            'temporal_coverage': {'type': 'literal', 'value': '2015-05-27/2015-06-20'},
            'id': {'type': 'literal', 'value': 'urn:uuid:696f9141-4e1a-5270-8c94-b0aabe0bbee7'},
            'keywords': {'type': 'literal', 'value': 'keyword1,keyword2,keyword3'}
        }
        result = self.search.convert_result(test_result)
        result.urls.sort()
        self.assertIsInstance(result, search.SearchResult)
        self.assertEqual(result.urls, ['url1', 'url2'])
        self.assertEqual(result.keywords, ['keyword1', 'keyword2', 'keyword3'])
        self.assertEqual(result.source, "Gleaner")


class TestSearchResultSet(unittest.TestCase):
    def test_equal(self):
        result1 = search.SearchResult(id='a', score=3)
        result2 = search.SearchResult(id='b', score=1)
        result3 = search.SearchResult(id='c', score=2)
        result4 = search.SearchResult(id='d', score=0)

        results = [result1, result2, result3]

        a = search.SearchResultSet(
            total_results=42, page_start=9, results=results)
        b = search.SearchResultSet(
            total_results=42, page_start=9, results=results)
        c = search.SearchResultSet(
            total_results=3, page_start=9, results=results)
        d = search.SearchResultSet(
            total_results=42, page_start=0, results=results)
        e = search.SearchResultSet(
            total_results=42, page_start=9, results=[result2, result3, result4])

        self.assertEqual(a, b)
        self.assertEqual(a, a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, d)
        self.assertNotEqual(a, e)
        self.assertNotEqual(c, b)

    def test_collate(self):
        result1 = search.SearchResult(id='a', score=3)
        result2 = search.SearchResult(id='b', score=1)
        result3 = search.SearchResult(id='c', score=2)
        result4 = search.SearchResult(id='d', score=0)

        results_a = [result1, result2]

        results_b = [result3, result4]

        a = search.SearchResultSet(
            total_results=2, page_start=3, results=results_a)
        b = search.SearchResultSet(
            total_results=2, page_start=0, results=results_b)

        c = search.SearchResultSet.collate(a, b)

        expected = search.SearchResultSet(
            total_results=4,
            page_start=0,
            results=[
                result1,
                result3,
                result2,
                result4
            ])

        self.assertEqual(c, expected)
