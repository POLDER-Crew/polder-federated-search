from flask import render_template, request

from app import app
from app.search.dataone import SolrDirectSearch

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def text_search():
    text = request.args.get('text')
    dataone = SolrDirectSearch()
    return dataone.text_search(q=text)
