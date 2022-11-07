from datetime import date
import unittest
import json
import requests
import requests_mock
from urllib.parse import unquote
from app.search import dataone, search

test_response = json.loads(
    '{"response": {"numFound": 100, "start": 1, "maxScore": 0.0, "docs": [{"some": "result", "score": 0, "id": "test1","author": "anonymous1"}, {"another": "result", "score": 0, "id": "test2","author": "anonymous2"}]}}')


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
            total_results=100,
            available_pages=2,
            page_number=2,
            results=[
                search.SearchResult(score=0, id="test1", source="DataONE"),
                search.SearchResult(score=0, id="test2", source="DataONE"),
            ]

        )
        results = self.search.text_search(text='test', page_number=2)
        self.assertEqual(results, expected)

        # Did we make the query we expected?
        solr_url = m.request_history[0].url
        self.assertIn('&q=test', solr_url)

        # Did we add the latitude filter?
        self.assertIn(
            f'&fq={dataone.SolrDirectSearch.LATITUDE_FILTER}',
            unquote(solr_url)
        )

        # Did we include the filter for duplicates?
        self.assertIn(dataone.SolrDirectSearch.DUPLICATE_FILTER,
                      unquote(solr_url))

        # Did we get the paging right?
        self.assertIn('?start=50', unquote(solr_url))

    @requests_mock.Mocker()
    def test_date_filter_none(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )
        expected = search.SearchResultSet(
            total_results=100,
            available_pages=2,
            page_number=0,
            results=[
                search.SearchResult(score=0, id="test1", source="DataONE"),
                search.SearchResult(score=0, id="test2", source="DataONE"),
            ]

        )
        results = self.search.date_filter_search()
        self.assertEqual(results, expected)

        # Did we make the query we expected?
        solr_url = unquote(m.request_history[0].url)
        self.assertIn("beginDate:[* TO NOW] AND endDate:[* TO NOW])", solr_url)

        # Did we add the latitude filter?
        self.assertIn(
            f'{dataone.SolrDirectSearch.LATITUDE_FILTER}',
            solr_url
        )

        # Did we include the filter for duplicates?
        self.assertIn(dataone.SolrDirectSearch.DUPLICATE_FILTER, solr_url)

    @requests_mock.Mocker()
    def test_date_filter_start_min(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        results = self.search.date_filter_search(start_min=date(1999, 3, 23))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[1999-03-23T00:00:00Z TO NOW] AND endDate:[* TO NOW])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_start_max(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        results = self.search.date_filter_search(start_max=date(1999, 3, 23))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[* TO 1999-03-23T23:59:59.999999Z] AND endDate:[* TO NOW])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_start_both(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        results = self.search.date_filter_search(
            start_min=date(1980, 1, 1), start_max=date(1999, 3, 23))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[1980-01-01T00:00:00Z TO 1999-03-23T23:59:59.999999Z] AND endDate:[* TO NOW])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_end_min(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )
        results = self.search.date_filter_search(
            end_min=date(2002, 1, 12))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[* TO NOW] AND endDate:[2002-01-12T00:00:00Z TO NOW])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_end_max(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )
        results = self.search.date_filter_search(
            end_max=date(2002, 1, 12))
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[* TO NOW] AND endDate:[* TO 2002-01-12T23:59:59.999999Z])", solr_url)

    @requests_mock.Mocker()
    def test_date_filter_all(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        results = self.search.date_filter_search(
            start_min=date(1980, 8, 4),
            start_max=date(1999, 3, 23),
            end_min=date(2001, 1, 1),
            end_max=date(2020, 12, 31)
        )
        solr_url = unquote(m.request_history[0].url)
        self.assertIn(
            "beginDate:[1980-08-04T00:00:00Z TO 1999-03-23T23:59:59.999999Z] AND endDate:[2001-01-01T00:00:00Z TO 2020-12-31T23:59:59.999999Z])", solr_url)

    @requests_mock.Mocker()
    def test_combined_search(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            json=test_response
        )

        expected = search.SearchResultSet(
            total_results=100,
            available_pages=2,
            page_number=0,
            results=[
                search.SearchResult(score=0, id="test1", source="DataONE"),
                search.SearchResult(score=0, id="test2", source="DataONE"),
            ]

        )

        results = self.search.combined_search(
            text="test",
            start_min=date(1980, 8, 4),
            start_max=date(1999, 3, 23),
            end_min=date(2001, 1, 1),
            end_max=date(2020, 12, 31)
        )
        self.assertEqual(results, expected)

        # Did we make the query we expected?
        solr_url = unquote(m.request_history[0].url)
        self.assertIn('&q=test', solr_url)
        self.assertIn(
            "beginDate:[1980-08-04T00:00:00Z TO 1999-03-23T23:59:59.999999Z] AND endDate:[2001-01-01T00:00:00Z TO 2020-12-31T23:59:59.999999Z])", solr_url)

        # Did we add the latitude filter?
        self.assertIn(
            f'&fq={dataone.SolrDirectSearch.LATITUDE_FILTER}', solr_url)

        # Did we include the filter for duplicates?
        self.assertIn(dataone.SolrDirectSearch.DUPLICATE_FILTER, solr_url)

    @requests_mock.Mocker()
    def test_search_error(self, m):
        m.get(
            dataone.SolrDirectSearch.ENDPOINT_URL,
            status_code=500
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            results = self.search.text_search(text='test')

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

    
    def test_search_author_name(self):
        arguments = {'text': 'ice', 'author': 'anonyous', 'page_number': 1, 'start_min': None, 'start_max': None, 'end_min': None, 'end_max': None}

        result = dataone.SolrDirectSearch.build_query("&q=originText:", 0)
        self.assertIn("&q=originText:", result)

    def test_page_size(self):
        result = dataone.SolrDirectSearch.build_query("", 0)
        self.assertIn("?start=0", result)
        result = dataone.SolrDirectSearch.build_query("", -42)
        self.assertIn("?start=0", result)
        result = dataone.SolrDirectSearch.build_query("", 25)
        self.assertIn(f"?start={dataone.SolrDirectSearch.PAGE_SIZE * 24}", result)

        dataone.PAGE_SIZE = 32
        result = dataone.SolrDirectSearch.build_query("", 3)
        self.assertIn(f"?start={dataone.SolrDirectSearch.PAGE_SIZE * 2}", result)

        # Set it back to the default so we do not get random test failures
        dataone.PAGE_SIZE = search.SearcherBase.PAGE_SIZE

    def test_convert_full_result(self):
        test_result = {
            'webUrl': ['url1', 'url2', 'url3'],
            'contentUrl': {'value': ['url5', 'url6', 'url7']},
            'seriesId': 'doi:test',
            'score': 5,
            'title': 'A title',
            'id': 'An id',
            'abstract': 'An abstract',
            'placeKey': 'a location',
            'keywords': ['keyword1', 'keyword2', 'keyword3'],
            'origin': 'an origin',
            'beginDate': '2016-01-01T00:00:00Z',
            'endDate': '2016-12-31T00:00:00Z'
        }
        result = self.search.convert_result(test_result)
        result.urls.sort()
        result.keywords.sort()
        self.assertEqual(result.score, 5)
        self.assertEqual(
            result.urls, ['https://search.dataone.org/view/An%20id', 'url1', 'url2', 'url3', 'url5', 'url6', 'url7'])
        self.assertEqual(result.title, 'A title'),
        self.assertEqual(result.id, ['An id'])
        self.assertEqual(result.abstract, 'An abstract')
        self.assertEqual(result.geometry['text'], 'a location')
        self.assertEqual(result.keywords, ['keyword1', 'keyword2', 'keyword3'])
        self.assertEqual(result.doi, 'doi:test')
        self.assertEqual(result.origin, 'an origin')
        self.assertEqual(result.temporal_coverage, [
                         '2016-01-01 to 2016-12-31'])

    def test_convert_sparse_result(self):
        test_result = {
            'score': 4,
            'seriesId': 'test',
            'id': 'test1'
        }
        result = self.search.convert_result(test_result)
        self.assertEqual(result.score, 4)
        self.assertEqual(result.doi, None)
        self.assertEqual(result.source, 'DataONE')
        self.assertEqual(result.id, ['test1'])
        self.assertEqual(
            result.urls, ['https://search.dataone.org/view/test1'])

    def test_Bounding_box_geometry(self):
        self.search.max_score = 10
        # testing for a polygon
        test_result1 = {
            'id': 'test1',
            'seriesId': 'doi:test',
            'southBoundCoord': 29.7,
            'northBoundCoord': 90.0,
            'westBoundCoord': -180.0,
            'score': 4,
            'eastBoundCoord': 180.0,
            'placeKey': 'test place'
        }
        test_obj_1 = self.search.convert_result(test_result1)
        self.assertEqual(test_obj_1.geometry['text'], 'test place')
        self.assertEqual(
            test_obj_1.geometry['geometry_collection'].type, 'Polygon')
        self.assertEqual(test_obj_1.geometry['geometry_collection'].coordinates, [
                         [(180.0, 29.7), (180.0, 90.0), (-180.0, 90.0), (-180.0, 29.7), (180.0, 29.7)]])
        test_result2 = {
            'id': 'test1',
            'score': 4,
            'seriesId': 'doi:test',
            'southBoundCoord': 76.7067,
            'northBoundCoord': 76.7067,
            'westBoundCoord': -105.5341,
            'eastBoundCoord': -105.5341,
            'placeKey': 'test place two'

        }

        # Testing for a point
        test_obj_2 = self.search.convert_result(test_result2)
        self.assertEqual(test_obj_2.geometry['text'], 'test place two')

        self.assertEqual(
            test_obj_2.geometry['geometry_collection'].type, 'Point')
        self.assertEqual(
            test_obj_2.geometry['geometry_collection'].coordinates, (-105.5341, 76.7067))

    def test_original_datasource(self):

        # Testing a dataset with an original source
        test_result = {
            'id': 'test1',
            'score': 4,
            'seriesId': 'doi:test',
            'datasource': 'urn:node:ARCTIC',


        }
        test_obj = self.search.convert_result(test_result)
        self.assertEqual(test_obj.datasource['key'], 'ARCTIC')
        self.assertEqual(test_obj.datasource['name'], 'Arctic Data Center')
        self.assertEqual(test_obj.datasource['url'], 'https://arcticdata.io/')
        self.assertEqual(
            test_obj.datasource['logo'], 'https://raw.githubusercontent.com/DataONEorg/member-node-info/master/production/graphics/web/ARCTIC.png')

        # Testing a dataset with no original source
        test_result1 = {
            'id': 'test1',
            'score': 4,
            'seriesId': 'doi:test',

        }
        test_obj1 = self.search.convert_result(test_result1)
        self.assertEqual(test_obj1.datasource, {})
