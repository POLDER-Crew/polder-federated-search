class SearchResultSet:
    """ A class to represent a set of search results, so that we cna
    have a common representation between search endpoints and technologies.
    """

    def __init__(self, **kwargs):
        self.total_results = kwargs.pop('total_results', 0)
        self.page_start = kwargs.pop('page_start', 0)
        self.results = kwargs.pop('results', [])
        # todo: do we want a shape for each result too? Probably eventually.

    # To make writing tests easier, let's say result sets are
    # equal if their internal attributes are equal.
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
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
            a.results + b.results,
            # and sort them by score...
            key=lambda x: float(x['score']),
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

    def text_search(self, **kwargs):
        raise NotImplementedError
