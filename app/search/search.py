from pygeojson import Polygon

DOI_PREFIXES = [
    'doi:',
    'http://dx.doi.org/',
    'https://dx.doi.org/',
    "http://data.g-e-m.dk/datasets?doi="
]


class SearchResult:
    """ A class representing each search result, so that we can have
    a common representation between search endpoints and technologies.

    These objects should not be treated as mutable.
    """

    def __init__(self, **kwargs):
        if not 'id' in kwargs:
            raise ValueError('Search results must have one or more ids.')

        if not 'score' in kwargs:
            raise ValueError('Search results must have a score.')

        self.id = []
        self.title = kwargs.pop('title', None)
        self.urls = kwargs.pop('urls', [])
        self.abstract = kwargs.pop('abstract', "")
        self.keywords = kwargs.pop('keywords', [])
        self.origin = kwargs.pop('origin', [])
        # Can be a single item or a list
        identifier = kwargs.pop('id', None)
        if isinstance(identifier, list):
            self.id.extend(identifier)
        else:
            self.id.append(identifier)

        self.datasource = kwargs.pop('datasource', None)
        self.geometry = kwargs.pop('geometry', '')
        self.author = kwargs.pop('author', [])
        self.license = kwargs.pop('license', None)
        # May or may not be the same as the ID
        self.doi = kwargs.pop('doi', None)
        self.spatial_coverage = kwargs.pop('spatial_coverage', None)
        self.temporal_coverage = kwargs.pop(
            'temporal_coverage', "").split(', ')
        self.score = float(kwargs.pop('score'))
        # Good for debugging
        self.source = kwargs.pop('source', 'Anonymous')

        # Format and remove blank terms and duplicates
        self.temporal_coverage = [
            t.replace('/', ' to ') for t in self.temporal_coverage if t]
        self.keywords = [k for k in self.keywords if k]
        self.author = [a for a in self.author if a]
        self.urls = list(set(x for x in self.urls if x))

        # If we have a DOI somewhere, use it as much as possible
        if not self.doi:
            candidates = self.id + self.urls
            for x in DOI_PREFIXES:
                if any((match := url).startswith(x) for url in candidates):
                    self.doi = 'doi:' + match.lstrip(x)
                    break

    """ Methods to make these sortable """

    def __lt__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

    def __ge__(self, other):
        return self.score >= other.score

    """ Methods to make these hashable """

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return self.__hash__ == other.__hash__

    def __ne__(self, other):
        return self.__hash__ != other.__hash__

    """ So debugging is a bit easier """

    def __str__(self):
        return f"Search Result from {self.source}: {self.id} with score {self.score}"

    """ Helper to convert a bounding box (common in search results) to a GeoJSON Polygon """
    @staticmethod
    def polygon_from_box(boundingbox):
        # Make a polygon with points in a counter clockwise motion and close
        # the polygon by ending with the starting point
        return Polygon(
            coordinates=[
                [(boundingbox['east'], boundingbox['south']),
                 (boundingbox['east'], boundingbox['north']),
                    (boundingbox['west'], boundingbox['north']),
                    (boundingbox['west'], boundingbox['south']),
                    (boundingbox['east'], boundingbox['south'])]
            ]
        )


class SearchResultSet:
    """ A class to represent a set of search results, so that we can
    have a common representation between search endpoints and technologies.
    """

    def __init__(self, **kwargs):
        self.total_results = kwargs.pop('total_results', 0)
        self.available_pages = kwargs.pop('available_pages', 0)

        # NOTE: Page numbers start counting from 1, because this number gets exposed
        # to the user, and people who are not programmers are weirded out by 0-indexed things
        self.page_number = kwargs.pop('page_number', 1)
        self.results = kwargs.pop('results', [])
        # todo: do we want a shape for each result too? Probably eventually.

    # To make writing tests easier, let's say result sets are
    # equal if their internal attributes are equal, and the
    # representations of their search results are equal.
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.total_results == other.total_results and
                self.page_number == other.page_number and
                self.available_pages == other.available_pages and
                len(self.results) == len(other.results) and
                all(
                    (
                        self.results[i].id == o.id and
                        self.results[i].score == o.score and
                        self.results[i].source == o.source and
                        self.results[i].title == o.title
                    ) for i, o in enumerate(other.results)
                )
            )

        else:
            return False

    @staticmethod
    def collate(a, b):
        """ Takes two SearchResultSets and combines them into one, by:
        - summing the total results
        - taking the lesser of the two page start values (todo: is this how we should do it?)
        - combining the result sets and sorting them by score
        """
        results = sorted(
            # put together our results lists...
            # By turning them into a set first and the
            # a list, we remove duplicates
            list(set(a.results + b.results)),
            # in descending order.
            reverse=True
        )
        return SearchResultSet(
            total_results=a.total_results + b.total_results,
            available_pages=max(a.available_pages, b.available_pages),
            page_number=min(a.page_number, b.page_number),
            results=results
        )


class SearcherBase:
    """ A base class for talking to search endpoints."""
    ENDPOINT_URL = ""
    PAGE_SIZE = 50

    @staticmethod
    def build_query(user_query="", page_number=1):
        """ Builds a query string for the search endpoint using the given parameters. user_query is a string that can
            be inserted in the query string in the appropriate place for this particular search endpoint.
            Page number starts from 1 because it is a value exposed to the user.
            This is a helper function for the search methods.
        """
        raise NotImplementedError

    def text_search(self, **kwargs):
        """ Makes a call to some search endpoint with the relevant text query
            Actual supported arguments should look something like text=None, page_number=0
        """
        raise NotImplementedError

    def date_filter_search(self, **kwargs):
        """ Makes a call to some search endpoint with the relevant date filter query
            Actual supported arguments should look something like this, if we were to write them out:
            start_min=None, start_max=None, end_min=None, end_max=None, page_number=0
        """
        raise NotImplementedError

    def combined_search(self, **kwargs):
        """  The search that will most commonly get used in the UI - a combination of
             all of the search methods.
            Actual supported arguments should look something like this, if we were to write them out:
            text=None, start_min=None, start_max=None, end_min=None, end_max=None, page_number=0
        """
        raise NotImplementedError

    def convert_result(self, result):
        """
        Convert an individual result from the underlying search endpoint to
        a SearchResult object.
        Used as a map on the set of results that the endpoint returns."""
        raise NotImplementedError

    def convert_results(self, raw_result_set):
        """
        A convenience method; takes in a raw result set and returns a list
        of SearchResult objects.
        """
        return list(map(self.convert_result, raw_result_set))
