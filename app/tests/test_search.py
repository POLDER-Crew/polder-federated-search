import unittest
import requests
import requests_mock
from urllib.parse import unquote

from app.search import dataone

test_response = "[{'some': result}], {'another': result}"

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
