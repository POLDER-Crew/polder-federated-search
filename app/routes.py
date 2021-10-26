from flask import render_template, request
import json

from app import app
from app.search.dataone import SolrDirectSearch
from app.search.gleaner import GleanerSearch

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def text_search():
    text = request.args.get('text')
    dataone_results = SolrDirectSearch().text_search(q=text)
    gleaner_results = GleanerSearch().text_search(q=text)

    dataone_number = dataone_results['numFound']
    dataone_start = dataone_results['start']

    results = sorted(
        # put together our results lists...
        dataone_results['docs'] + gleaner_results,
        # and sort them by score...
        key=lambda x: float(x['score']),
        # in descending order.
        reverse=True
    )
    return json.dumps(results)

    # todo: I have no idea how SPARQL / Blazegraph relevance scores and Solr relevance scores
    # compare to each other, so some calibration will be needed.
