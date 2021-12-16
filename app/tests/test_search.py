import unittest
from unittest.mock import patch, mock_open, Mock
import json
import re
import requests
import requests_mock
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError
from urllib.parse import unquote
from urllib.response import addinfourl

from app.search import dataone, gleaner, search

test_response = json.loads(
    '{"response": {"numFound": 1, "start": 5, "maxScore": 0.0, "docs": [{"some": "result", "score": "0", "id": "test1"}, {"another": "result", "score": "0", "id": "test2"}]}}')


class TestSolrDirectSearch(unittest.TestCase):
    def setUp(self):
        self.search = dataone.SolrDirectSearch()

    @requests_mock.Mocker()
    def test_text_search(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )
        expected = search.SearchResultSet(
            total_results=1,
            page_start=5,
            results=[
                search.SearchResult(score=0, id="test1", source="DataONE"),
                search.SearchResult(score=0, id="test2", source="DataONE"),
            ]

        )
        results = self.search.text_search('test')
        self.assertEqual(results, expected)

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
            dataone.SolrDirectSearch.ENDPOINT_URL,
            status_code=500
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            results = self.search.text_search('test')

    @requests_mock.Mocker()
    def test_missing_kwargs(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )
        results = self.search.text_search()
        self.assertIn(
            f'&fq={dataone.SolrDirectSearch.LATITUDE_FILTER}',
            unquote(m.request_history[0].url)
        )


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
            'id': {'type': 'literal', 'value': 'urn:uuid:696f9141-4e1a-5270-8c94-b0aabe0bbee7'}
        }
        result = self.search.convert_result(test_result)
        self.assertIsInstance(result, search.SearchResult)
        self.assertEqual(result.urls, ['url1', 'url2'])
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


class TestSearchResult(unittest.TestCase):
    def test_init(self):
        kwargs_dict = {
            'title': 'A test title',
            'urls': ['url1', 'url2', 'url3'],
            'abstract': """Now, we're going to fluff this cloud. Trees get lonely too, so we'll give him a little friend. Poor old tree. Every day I learn. Put your feelings into it, your heart, it's your world.

                        Let your heart take you to wherever you want to be. Absolutely no pressure. You are just a whisper floating across a mountain. Once you learn the technique, ohhh! Turn you loose on the world; you become a tiger. Let's have a happy little tree in here. Trees cover up a multitude of sins. And maybe, maybe, maybe...

                        With something so strong, a little bit can go a long way. Just go out and talk to a tree. Make friends with it. Decide where your cloud lives. Maybe he lives right in here. You're meant to have fun in life. Maybe, just to play a little, we'll put a little tree here. There it is.

                        It's important to me that you're happy. That's a crooked tree. We'll send him to Washington. Just go back and put one little more happy tree in there.

                        This is probably the greatest thing to happen in my life - to be able to share this with you. Have fun with it. We don't make mistakes we just have happy little accidents.

                        Play with the angles. La- da- da- da- dah. Just be happy. If you do too much it's going to lose its effectiveness.

                        The only prerequisite is that it makes you happy. If it makes you happy then it's good. Everybody needs a friend. We have all at one time or another mixed some mud. Just let go - and fall like a little waterfall.

                        """,
            'id': 'an identifier',
            'spatial_coverage': 'some spatial coverage object',
            'temporal_coverage': 'some temporal coverage object',
            'score': 42
        }
        test_obj = search.SearchResult(**kwargs_dict)
        self.assertEqual(test_obj.title, kwargs_dict['title'])
        self.assertEqual(test_obj.urls, kwargs_dict['urls'])
        self.assertEqual(test_obj.abstract, kwargs_dict['abstract'])
        self.assertEqual(test_obj.id, kwargs_dict['id'])
        self.assertEqual(test_obj.spatial_coverage,
                         kwargs_dict['spatial_coverage'])
        self.assertEqual(test_obj.temporal_coverage,
                         kwargs_dict['temporal_coverage'])
        self.assertEqual(test_obj.score, kwargs_dict['score'])

    def test_init_missing_id(self):
        with self.assertRaises(ValueError):
            test_obj = search.SearchResult(score=7)

    def test_init_missing_score(self):
        with self.assertRaises(ValueError):
            test_obj = search.SearchResult(id='some id')

    def test_init_defaults(self):
        test_obj = search.SearchResult(id='test test test', score=10.5)
        self.assertEqual(test_obj.title, None)
        self.assertEqual(test_obj.urls, [])
        self.assertEqual(test_obj.abstract, "")
        self.assertEqual(test_obj.id, 'test test test')
        self.assertEqual(test_obj.spatial_coverage, None)
        self.assertEqual(test_obj.temporal_coverage, None)
        self.assertEqual(test_obj.score, 10.5)

    def test_operators(self):
        a = search.SearchResult(id='a', score=1)
        b = search.SearchResult(id='b', score=2)
        c = search.SearchResult(id='c', score=1)
        d = search.SearchResult(id='c', score=1)

        self.assertTrue(a < b)
        self.assertFalse(b < a)
        self.assertTrue(b > a)
        self.assertFalse(a > b)
        self.assertTrue(b >= c)
        self.assertTrue(a >= c)
        self.assertTrue(c >= a)
        self.assertFalse(c >= b)
        self.assertFalse(a == b)
        self.assertFalse(d == c)
        self.assertTrue(a == a)
        self.assertTrue(a is a)
