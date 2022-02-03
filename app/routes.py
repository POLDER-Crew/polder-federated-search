from flask import render_template, request
from datetime import date

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
    try:
        start_min = kwargs.pop('start_min', None)
        if start_min:
            start_min = date.fromisoformat(start_min)

        start_max = kwargs.pop('start_max', None)
        if start_max:
            start_max = date.fromisoformat(start_max)

        end_min = kwargs.pop('end_min', None)
        if end_min:
            end_min = date.fromisoformat(end_min)

        end_max = kwargs.pop('end_max', None)
        if end_max:
            end_max = date.fromisoformat(end_max)
    except ValueError as ve:  # we got some invalid dates
        return str(ve), 400

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
