from flask import render_template, request

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch
from app.search.search import SearchResultSet


@app.route('/')
def home():
    return render_template('index.html')


def _do_combined_search(template, **kwargs):
    text = kwargs.pop('text', None)

    # These all need to be date objects
    start_min = kwargs.pop('start_min', None)
    start_max = kwargs.pop('start_max', None)
    end_min = kwargs.pop('end_min', None)
    end_max = kwargs.pop('end_max', None)

    dataone = SolrDirectSearch().combined_search(
        text, start_min, start_max, end_min, end_max)
    gleaner = GleanerSearch(endpoint_url=app.config['GLEANER_ENDPOINT_URL']).combined_search(
        text, start_min, start_max, end_min, end_max)

    results = SearchResultSet.collate(dataone, gleaner)

    return render_template(template, result_set=results)


@app.route('/search')
# Redirect to a stand-alone page to display results
def nojs_combined_search():
    return _do_combined_search('search.html', **request.args)


@app.route('/api/search')
def combined_search():
    return _do_combined_search('results.html', **request.args)
