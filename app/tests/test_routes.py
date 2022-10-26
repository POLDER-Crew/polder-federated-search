import unittest
from unittest.mock import patch
from datetime import date
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

    def test_home(self):
        client = app.test_client()
        response = client.get('/polder')

        self.assertEqual(response.status, '308 PERMANENT REDIRECT')

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_nojs_combined_search(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        start_min = date(2008, 1, 1)
        start_max = date(2010, 5, 12)
        end_min = date(2010, 5, 13)
        end_max = date(2099, 5, 5)

        expected = {
            'text': 'Greenland',
            'author': None,
            'page_number': 2,
            'start_min': start_min,
            'start_max': start_max,
            'end_min': end_min,
            'end_max': end_max
            }

        with app.test_client() as client:
            response = client.get(
                '/search?start_max=2010-05-12&text=Greenland&end_min=2010-05-13&start_min=2008-01-01&end_max=2099-05-05&page=2')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_combined_search(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        start_min = date(2008, 1, 1)
        start_max = date(2010, 5, 12)
        end_min = date(2010, 5, 13)
        end_max = date(2099, 5, 5)

        expected = {
            'text': 'walrus',
            'author': None,
            'page_number': 5,
            'start_min': start_min,
            'start_max': start_max,
            'end_min': end_min,
            'end_max': end_max
        }

        with app.test_client() as client:
            response = client.get(
                '/api/search?end_min=2010-05-13&start_max=2010-05-12&start_min=2008-01-01&end_max=2099-05-05&text=walrus&page=5')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_defaults(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        expected = {
            'text': None,
            'author': None,
            'page_number': 1,
            'start_min': None,
            'start_max': None,
            'end_min': None,
            'end_max': None
            }

        with app.test_client() as client:
            response = client.get('/api/search')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_page(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        expected = {
            'text': None,
            'author': None,
            'page_number': 42,
            'start_min': None,
            'start_max': None,
            'end_min': None,
            'end_max': None
            }

        with app.test_client() as client:
            response = client.get('/api/search?page=42')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)


    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_text_only(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        expected = {
            'text': 'walrus',
            'author': None,
            'page_number': 1,
            'start_min': None,
            'start_max': None,
            'end_min': None,
            'end_max': None
            }

        with app.test_client() as client:
            response = client.get('/api/search?text=walrus')
            self.assertEqual(response.request.args['text'], 'walrus')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_dates_only(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        start_min = date(2008, 1, 1)
        start_max = date(2010, 5, 12)
        end_min = date(2010, 5, 13)
        end_max = date(2099, 5, 5)

        expected = {
            'text': None,
            'author': None,
            'page_number': 1,
            'start_min': start_min,
            'start_max': None,
            'end_min': None,
            'end_max': None
        }

        with app.test_client() as client:
            response = client.get('/api/search?start_min=2008-01-01')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

            response = client.get('/api/search?start_max=2010-05-12')
            self.assertEqual(response.status, '200 OK')

            expected['start_min'] = None
            expected['start_max'] =  start_max

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

            response = client.get('/api/search?end_min=2010-05-13')
            self.assertEqual(response.status, '200 OK')

            expected['end_min'] = end_min
            expected['start_max'] =  None

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

            response = client.get('/api/search?end_max=2099-05-05')
            self.assertEqual(response.status, '200 OK')

            expected['end_min'] = None
            expected['end_max'] =  end_max

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

            response = client.get(
                '/api/search?start_min=2008-01-01&end_max=2099-05-05')
            self.assertEqual(response.status, '200 OK')

            expected['start_min'] = start_min
            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_invalid_page_number(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        with app.test_client() as client:
            response = client.get('/api/search?page=h4xx0r')
            self.assertEqual(response.status, '400 BAD REQUEST')

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_invalid_date(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        with app.test_client() as client:
            response = client.get('/api/search?start_min=2008-13-13')
            self.assertEqual(response.status, '400 BAD REQUEST')

    @patch('app.search.dataone.SolrDirectSearch.combined_search')
    @patch('app.search.gleaner.GleanerSearch.combined_search')
    def test_empty_dates(self, gleaner, dataone):
        gleaner.return_value = self.mock_result_set
        dataone.return_value = self.mock_result_set

        start_min = date(2008, 1, 1)

        expected = {
            'text': None,
            'author': None,
            'page_number': 1,
            'start_min': start_min,
            'start_max': None,
            'end_min': None,
            'end_max': None
        }

        with app.test_client() as client:
            response = client.get('/api/search?start_min=2008-01-01&start_max=')
            self.assertEqual(response.status, '200 OK')

            gleaner.assert_called_with(**expected)
            dataone.assert_called_with(**expected)
