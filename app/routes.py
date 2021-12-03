from flask import render_template, request

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch
from app.search.search import SearchResultSet


@app.route('/')
def home():
    return render_template('index.html')

def _do_text_search(text, template):
    dataone = SolrDirectSearch().text_search(q=text)
    gleaner = GleanerSearch(endpoint_url=app.config['GLEANER_ENDPOINT_URL']).text_search(q=text)

    results = SearchResultSet.collate(dataone, gleaner)
    return render_template(template, result_set=results)
    # todo: I have no idea how SPARQL / Blazegraph relevance scores and
    # Solr relevance scores
    # compare to each other, so some calibration will be needed.


@app.route('/search')
# Redirect to a stand-alone page to display results
def nojs_text_search():
    text = request.args.get('text')
    return _do_text_search(text, 'search.html')


@app.route('/api/search')
def text_search():
    text = request.args.get('text')
    return _do_text_search(text, 'results.html')
