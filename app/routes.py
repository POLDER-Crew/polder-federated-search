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
    dataone = SolrDirectSearch().text_search(q=text)
    gleaner = GleanerSearch().text_search(q=text)

    results = sorted(
        # put together our results lists...
        dataone.results + gleaner.results,
        # and sort them by score...
        key=lambda x: float(x['score']),
        # in descending order.
        reverse=True
    )
    return json.dumps(results)

    # todo: I have no idea how SPARQL / Blazegraph relevance scores and Solr relevance scores
    # compare to each other, so some calibration will be needed.
