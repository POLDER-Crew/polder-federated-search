

class SearchResult:
    """ A class representing each search result, so that we can have
    a common representation between search endpoints and technologies.

    These objects should not be treated as mutable.
    """

    def __init__(self, **kwargs):
        if not 'id' in kwargs:
            raise ValueError('Search results must have an id.')

        if not 'score' in kwargs:
            raise ValueError('Search results must have a score.')

        self.title = kwargs.pop('title', None)
        self.urls = kwargs.pop('urls', [])
        self.abstract = kwargs.pop('abstract', "")
        self.keywords = kwargs.pop('keywords', [])
        self.origin = kwargs.pop('origin', [])
        self.id = kwargs.pop('id')
        # May or may not be the same as the ID
        self.doi = kwargs.pop('doi', None)
        self.spatial_coverage = kwargs.pop('spatial_coverage', None)
        self.temporal_coverage = kwargs.pop('temporal_coverage', None)
        self.score = float(kwargs.pop('score'))
        # Good for debugging
        self.source = kwargs.pop('source', 'Anonymous')

        # If we have a DOI somewhere, use it as much as possible
        if not self.doi and self.id and self.id.startswith('doi:'):
            self.doi = self.id

        self.urls = list(set(self.urls))

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


class SearchResultSet:
    """ A class to represent a set of search results, so that we can
    have a common representation between search endpoints and technologies.
    """

    def __init__(self, **kwargs):
        self.total_results = kwargs.pop('total_results', 0)
        self.page_start = kwargs.pop('page_start', 0)
        self.results = kwargs.pop('results', [])
        # todo: do we want a shape for each result too? Probably eventually.

    # To make writing tests easier, let's say result sets are
    # equal if their internal attributes are equal, and the
    # representations of their search results are equal.
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.total_results == other.total_results and
                self.page_start == other.page_start and
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
            page_start=min(a.page_start, b.page_start),
            results=results
        )


class SearcherBase:
    """ A base class for talking to search endpoints."""
    ENDPOINT_URL = ""
    PAGE_SIZE = 50

    def text_search(self, text=None):
        """ Makes a call to some search endpoint with the relevant text query"""
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
