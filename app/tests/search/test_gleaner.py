from datetime import date
import unittest
from unittest.mock import patch, mock_open, Mock
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError
from urllib.response import addinfourl
from app.search import gleaner, search

count_result = {
    'total_results': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '200'}
}
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


class TestGleanerSearch(unittest.TestCase):
    def setUp(self):
        self.search = gleaner.GleanerSearch(endpoint_url="http://test")

        # Set up our mock SPARQLWrapper results. We have mocked out the query() method from
        # SPARQLWrapper, but that method returns an object that we immediately call convert() on,
        # and the results of that are what we work with.
        mock_convert = Mock(return_value={"results": {
            "bindings": [count_result, result1, result2]
        }})
        self.mock_query = Mock()
        self.mock_query.convert = mock_convert

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_text_search_none(self, query):
        query.return_value = self.mock_query
        results = self.search.text_search()
        self.assertNotIn('luc:query', self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_text_search(self, query):
        query.return_value = self.mock_query

        # Do the actual test
        expected = search.SearchResultSet(
            total_results=200,
            available_pages=4,
            page_number=5,
            results=[
                self.search.convert_result(result1),
                self.search.convert_result(result2)
            ]

        )
        results = self.search.text_search(text='test', page_number=5)
        self.assertEqual(results, expected)
        self.assertIn("luc:query '''test'''", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_none(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search()
        self.assertNotIn('FILTER(?start_date', self.search.query)
        self.assertNotIn('FILTER(?end_date', self.search.query)
        self.assertNotIn('CONTAINS(?temporal_coverage', self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_start_min(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(start_min=date(1999, 1, 1))
        self.assertIn(
            "FILTER(?start_date >= '1999-01-01'^^xsd:date)", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_start_max(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(start_max=date(1999, 1, 1))
        self.assertIn(
            "FILTER(?start_date <= '1999-01-01'^^xsd:date)", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_start_both(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(
            start_min=date(1999, 1, 1), start_max=date(2020, 3, 3))
        self.assertIn(
            "FILTER(?start_date >= '1999-01-01'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?start_date <= '2020-03-03'^^xsd:date)", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_end_min(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(end_min=date(1999, 1, 1))
        self.assertIn(
            "FILTER(?end_date >= '1999-01-01'^^xsd:date)", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_end_max(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(end_max=date(1999, 1, 1))
        self.assertIn(
            "FILTER(?end_date <= '1999-01-01'^^xsd:date)", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_date_filter_all(self, query):
        query.return_value = self.mock_query
        results = self.search.date_filter_search(
            start_min=date(1999, 1, 1),
            start_max=date(2020, 3, 3),
            end_min=date(2001, 9, 12),
            end_max=date(2023, 3, 31),
            page_number=2
        )
        self.assertIn(
            "FILTER(?start_date >= '1999-01-01'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?start_date <= '2020-03-03'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?end_date >= '2001-09-12'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?end_date <= '2023-03-31'^^xsd:date)", self.search.query)
        self.assertIn("OFFSET 50", self.search.query)

    @patch('SPARQLWrapper.SPARQLWrapper.query')
    def test_combined_search(self, query):
        query.return_value = self.mock_query

        # Do the actual test
        expected = search.SearchResultSet(
            total_results=200,
            available_pages=4,
            page_number=3,
            results=[
                self.search.convert_result(result1),
                self.search.convert_result(result2)
            ]

        )
        results = self.search.combined_search(
            text="test",
            start_min=date(1999, 1, 1),
            start_max=date(2020, 3, 3),
            end_min=date(2001, 9, 12),
            end_max=date(2023, 3, 31),
            page_number=3
        )
        self.assertEqual(results, expected)

        self.assertIn("luc:query '''test'''", self.search.query)
        self.assertIn(
            "FILTER(?start_date >= '1999-01-01'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?start_date <= '2020-03-03'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?end_date >= '2001-09-12'^^xsd:date)", self.search.query)
        self.assertIn(
            "FILTER(?end_date <= '2023-03-31'^^xsd:date)", self.search.query)
        self.assertIn("OFFSET 100", self.search.query)

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
            results = self.search.text_search(text='test')

    def test_page_size(self):
        result = gleaner.GleanerSearch.build_query(None, None, 0)
        self.assertIn("OFFSET 0", result)
        result = gleaner.GleanerSearch.build_query(None, None, -99)
        self.assertIn("OFFSET 0", result)
        result = gleaner.GleanerSearch.build_query(None, None, 25)
        self.assertIn(f"OFFSET {gleaner.GleanerSearch.PAGE_SIZE * 24}", result)

        gleaner.GleanerSearch.PAGE_SIZE = 32
        result = gleaner.GleanerSearch.build_query(None, None, 3)
        self.assertIn(f"OFFSET {gleaner.GleanerSearch.PAGE_SIZE * 2}", result)

        # Set it back to the default so we do not get random test failures
        gleaner.GleanerSearch.PAGE_SIZE = search.SearcherBase.PAGE_SIZE

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

    def test_convert_result_with_url_in_id(self):
        test_result = {
            'score': {'datatype': 'http://www.w3.org/2001/XMLSchema#double', 'type': 'literal', 'value': '0.375'},
            'abstract': {'type': 'literal', 'value': 'This data file contains information'},
            'title': {'type': 'literal', 'value': 'Iceflux trawl (SUIT & RMT) and ice stations'},
            'url': {'type': 'literal', 'value': 'url1'},
            'sameAs': {'type': 'literal', 'value': 'url2'},
            'spatial_coverage': {'type': 'literal', 'value': '-70.5397 -10.4515 -57.4443 0.018'},
            'temporal_coverage': {'type': 'literal', 'value': '2015-05-27/2015-06-20'},
            'id': {'type': 'literal', 'value': 'http://www.mycooldataset.com'},
            'keywords': {'type': 'literal', 'value': 'keyword1,keyword2,keyword3'}
        }
        result = self.search.convert_result(test_result)
        result.urls.sort()
        self.assertIsInstance(result, search.SearchResult)
        self.assertEqual(
            result.urls, ['http://www.mycooldataset.com', 'url1', 'url2'])
        self.assertEqual(result.keywords, ['keyword1', 'keyword2', 'keyword3'])
        self.assertEqual(result.source, "Gleaner")
