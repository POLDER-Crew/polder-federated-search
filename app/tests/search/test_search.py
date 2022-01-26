import unittest
from app.search import search





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
        test_obj.urls.sort()
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

    def test_init_doi(self):
        test_obj = search.SearchResult(id='doi:test_test', score=4)
        self.assertEqual(test_obj.id, 'doi:test_test')
        self.assertEqual(test_obj.doi, 'doi:test_test')
        self.assertEqual(test_obj.urls, [])

    def test_doi_urls(self):
        test_obj = search.SearchResult(
            id='doi:test_test', score=4, urls=['http://test1', 'http://dx.doi.org/test_test'])
        self.assertEqual(test_obj.id, 'doi:test_test')
        self.assertEqual(test_obj.doi, 'doi:test_test')
        test_obj.urls.sort()
        self.assertEqual(
            test_obj.urls, ['http://dx.doi.org/test_test', 'http://test1'])

        test_obj_2 = search.SearchResult(id='doi:test2_test2', score=4, urls=[
                                         'http://test1', 'http://doi.org/test2_test2'])
        self.assertEqual(test_obj_2.id, 'doi:test2_test2')
        self.assertEqual(test_obj_2.doi, 'doi:test2_test2')
        test_obj_2.urls.sort()
        self.assertListEqual(
            test_obj_2.urls, ['http://doi.org/test2_test2', 'http://test1'])

        test_existing_doi = search.SearchResult(
            id='doi:test3', score=1, doi='existing_value')
        self.assertEqual(test_existing_doi.id, 'doi:test3')
        self.assertEqual(test_existing_doi.doi, 'existing_value')
        self.assertListEqual(test_existing_doi.urls, [])

        test_doi_from_url = search.SearchResult(
            id='foo', score=4, urls=['http://test1', 'http://dx.doi.org/asdf'])
        self.assertEqual(test_doi_from_url.id, 'foo')
        self.assertEqual(test_doi_from_url.doi, 'doi:asdf')
        test_doi_from_url.urls.sort()
        self.assertEqual(
            test_doi_from_url.urls, ['http://dx.doi.org/asdf', 'http://test1'])

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
