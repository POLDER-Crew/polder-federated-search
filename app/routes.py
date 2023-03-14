import logging
from flask import redirect, render_template, request, url_for
from datetime import date
from sentry_sdk import capture_exception
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed, BadRequest

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch
from app.search.search import SearchResultSet

BAD_REQUEST_STATUS = 400

logger = logging.getLogger('app')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/polder/')
def polder():
    """This is for backward compatibility, because /polder has been sent out to
    a bunch of mailing lists.
    """
    return redirect(url_for('home'))


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/help/')
def help():
    return render_template('help.html')


def _get_date_from_args(arg_name, kwargs):
    arg_date = kwargs.pop(arg_name, None)
    if arg_date:
        return date.fromisoformat(arg_date)
    else:  # empty strings are also falsy and cause trouble
        return None


def _do_combined_search(template, **kwargs):
    sanitized_kwargs = {}
    sanitized_kwargs['text'] = kwargs.pop('text', None)
    sanitized_kwargs['author'] = kwargs.pop('author', None)

    try:
        # Human-readable pages start at 1
        sanitized_kwargs['page_number'] = int(kwargs.pop('page', 1))

        # These all need to be date objects
        sanitized_kwargs['start_min'] = _get_date_from_args(
            'start_min', kwargs)
        sanitized_kwargs['start_max'] = _get_date_from_args(
            'start_max', kwargs)
        sanitized_kwargs['end_min'] = _get_date_from_args('end_min', kwargs)
        sanitized_kwargs['end_max'] = _get_date_from_args('end_max', kwargs)

    # we got some invalid dates or a type %SYSTEMROOT%\\win.ini where an int should be
    except ValueError as ve:
        return str(ve), BAD_REQUEST_STATUS

    dataone = SolrDirectSearch().combined_search(**sanitized_kwargs)
    gleaner = GleanerSearch(
        endpoint_url=app.config['GLEANER_ENDPOINT_URL']).combined_search(**sanitized_kwargs)

    results = SearchResultSet.collate(dataone, gleaner)

    return render_template(template, result_set=results)


@app.route('/search')
# Redirect to a stand-alone page to display results
def nojs_combined_search():

    return _do_combined_search('search.html', **request.args)


@app.route('/api/search')
def combined_search():

    return _do_combined_search('results.html', **request.args)


@app.route('/api/count')
def get_count_repos():

    gleaner_total_count = GleanerSearch(
        endpoint_url=app.config['GLEANER_ENDPOINT_URL']).get_total_count()

    return str(gleaner_total_count)


@app.route('/api/sparql')
# A pass-through for our SPARQL endpoint, for partners to query directly.
def sparql():
    if not 'query' in request.args:
        return "Query parameter 'query' is required", BAD_REQUEST_STATUS
    query = request.args['query']
    result = GleanerSearch(
        endpoint_url=app.config['GLEANER_ENDPOINT_URL']).pass_through_query(query)
    return result


@app.errorhandler(NotFound)
def handle_404(e):
    return render_template("404.html", e=e), 404


@app.errorhandler(MethodNotAllowed)
@app.errorhandler(BadRequest)
# There are a lot of bots on the internet that try to post garbage
# to get-only routes, and other such shenanigans, and they are
# making lots of noise in Sentry.
# If we're running a dev server, it's good to see this error
# message because maybe we're trying to write a REST endpoint.
# But if we're in production, it's better to bypass it.
def handle_400_405(e):
    if app.debug == False:
        return render_template("500_generic.html", e=e)
    else:
        return handle_exception(e)


@app.errorhandler(Exception)
def handle_exception(e):
    # Record it in Sentry if we're in production
    if app.debug == False:
        capture_exception(e)
    else:
        logger.exception(
            "Exception while handling request for %s: %s", request.url, e)

    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    return render_template("500_generic.html", e=e), 500
