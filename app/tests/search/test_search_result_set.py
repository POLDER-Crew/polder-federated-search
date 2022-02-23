import unittest
from app.search import search

class TestSearchResultSet(unittest.TestCase):
    def test_equal(self):
        result1 = search.SearchResult(id='a', score=3)
        result2 = search.SearchResult(id='b', score=1)
        result3 = search.SearchResult(id='c', score=2)
        result4 = search.SearchResult(id='d', score=0)

        results = [result1, result2, result3]

        a = search.SearchResultSet(
            total_results=42, available_pages=4, page_number=9, results=results)
        b = search.SearchResultSet(
            total_results=42, available_pages=4, page_number=9, results=results)
        c = search.SearchResultSet(
            total_results=3, available_pages=4, page_number=9, results=results)
        d = search.SearchResultSet(
            total_results=42, available_pages=4, page_number=0, results=results)
        e = search.SearchResultSet(
            total_results=42, available_pages=4, page_number=9, results=[result2, result3, result4])

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
            total_results=2, available_pages=2, page_number=3, results=results_a)
        b = search.SearchResultSet(
            total_results=2, available_pages=1, page_number=0, results=results_b)

        c = search.SearchResultSet.collate(a, b)

        expected = search.SearchResultSet(
            total_results=4,
            available_pages=2,
            page_number=0,
            results=[
                result1,
                result3,
                result2,
                result4
            ])

        self.assertEqual(c, expected)
