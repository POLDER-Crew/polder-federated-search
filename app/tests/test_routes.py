import unittest
from unittest.mock import patch
from app import app
from app.search.search import SearchResultSet

from app.routes import home, combined_search, nojs_combined_search

app.testing = True

class TestRoutes(unittest.TestCase):
    def setUp(self):
        # Our mock searches have to return something. In this case, I'm making
        # them return empty result sets, because that isn't what we are interested
        # in testing right here. If we want to get fancy with processing them before
        # they go into the template, though, defining some test result sets like this
        # would be a great way to do it.

        self.mock_result_set = SearchResultSet()

    def test_home(self):
        client = app.test_client()
        response = client.get('/')

        self.assertEqual(response.status, '200 OK')

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_nojs_combined_search(self, gleaner, dataone):
        pass

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_combined_search(self, gleaner, dataone):
        pass

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_text_only(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        with app.test_client() as client:
            response = client.get('/api/search?text=walrus')
            self.assertEqual(response.request.args['text'], 'walrus')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with('walrus', None, None, None, None)
            dataone.assert_called_with('walrus', None, None, None, None)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_dates_only(self, gleaner, dataone):
        pass
