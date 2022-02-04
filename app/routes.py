from flask import render_template, request
from datetime import date

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch
from app.search.search import SearchResultSet

BAD_REQUEST_STATUS = 400

@app.route('/')
def home():
    return render_template('index.html')


def _get_date_from_args(arg_name, kwargs):
    arg_date = kwargs.pop(arg_name, None)
    if arg_date:
        return date.fromisoformat(arg_date)
    else:  # empty strings are also falsy and cause trouble
        return None


def _do_combined_search(template, **kwargs):
    text = kwargs.pop('text', None)

    # These all need to be date objects
    try:
        start_min = _get_date_from_args('start_min', kwargs)
        start_max = _get_date_from_args('start_max', kwargs)
        end_min = _get_date_from_args('end_min', kwargs)
        end_max = _get_date_from_args('end_max', kwargs)

    except ValueError as ve:  # we got some invalid dates
        return str(ve), BAD_REQUEST_STATUS

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
