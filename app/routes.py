from flask import render_template, request

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch
from app.search.search import SearchResultSet


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search')
def text_search():
    text = request.args.get('text')
    dataone = SolrDirectSearch().text_search(q=text)
    gleaner = GleanerSearch(endpoint_url=app.config['GLEANER_ENDPOINT_URL']).text_search(q=text)

    results = SearchResultSet.collate(dataone, gleaner)
    return render_template('results.html', result_set=results)

    # todo: I have no idea how SPARQL / Blazegraph relevance scores and
    # Solr relevance scores
    # compare to each other, so some calibration will be needed.
