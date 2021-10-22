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

    # todo: collate results
    return json.dumps(gleaner_results)
