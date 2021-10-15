from app import app
from app.search.dataone import DataOneSearch

@app.route('/')
def home():
    return 'POLDER Federated Search!'

@app.route('/search/<text>')
def text_search(text):
    dataone = DataOneSearch()
    return dataone.text_search(q="title:" + text)
