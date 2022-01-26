from datetime import date
import unittest
import json
import requests
import requests_mock
from urllib.parse import unquote
from app.search import dataone, search

test_response = json.loads(
    '{"response": {"numFound": 1, "start": 5, "maxScore": 0.0, "docs": [{"some": "result", "score": 0, "id": "test1"}, {"another": "result", "score": 0, "id": "test2"}]}}')


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
    def test_date_filter_none(self, m):
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
        results = self.search.date_filter_search()
        self.assertEqual(results, expected)

        # Did we make the query we expected?
        solr_url = unquote(m.request_history[0].url)
        self.assertIn("beginDate:[* TO NOW] OR endDate:[* TO NOW])", solr_url)

        # Did we add the latitude filter?
        self.assertIn(
            f'{dataone.SolrDirectSearch.LATITUDE_FILTER}',
            solr_url
        )

    @requests_mock.Mocker()
    def test_date_filter_start_min(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        results = self.search.date_filter_search(start_min=date(1999, 3, 23))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn("beginDate:[1999-03-23Z TO NOW] OR endDate:[* TO NOW])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_start_max(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

    @requests_mock.Mocker()
    def test_date_filter_start_both(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

    @requests_mock.Mocker()
    def test_date_filter_end_min(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

    @requests_mock.Mocker()
    def test_date_filter_end_max(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

    @requests_mock.Mocker()
    def test_date_filter_all(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
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

    def test_convert_full_result(self):
        self.search.max_score = 10

        test_result = {
            'webUrl': ['url1', 'url2', 'url3'],
            'dataUrl': 'url4',
            'contentUrl': {'value': ['url5', 'url6', 'url7']},
            'seriesId': 'doi:test',
            'score': 5,
            'title': 'A title',
            'id': 'An id',
            'abstract': 'An abstract',
            'placeKey': 'a location',
            'keywords': ['keyword1', 'keyword2', 'keyword3'],
            'origin': 'an origin',
        }
        result = self.search.convert_result(test_result)
        result.urls.sort()
        result.keywords.sort()
        self.assertEqual(result.score, 0.5)
        self.assertEqual(
            result.urls, ['url1', 'url2', 'url3', 'url4', 'url5', 'url6', 'url7'])
        self.assertEqual(result.title, 'A title'),
        self.assertEqual(result.id, 'An id')
        self.assertEqual(result.abstract, 'An abstract')
        self.assertEqual(result.spatial_coverage, 'a location')
        self.assertEqual(result.keywords, ['keyword1', 'keyword2', 'keyword3'])
        self.assertEqual(result.doi, 'doi:test')
        self.assertEqual(result.origin, 'an origin')

    def test_convert_sparse_result(self):
        self.search.max_score = 10

        test_result = {
            'score': 4,
            'seriesId': 'test'
        }
        result = self.search.convert_result(test_result)
        self.assertEqual(result.score, 0.4)
        self.assertEqual(result.doi, None)
        self.assertEqual(result.source, 'DataONE')
        self.assertEqual(result.id, None)
