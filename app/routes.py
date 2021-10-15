from app import app

@app.route('/')
def home():
    return 'POLDER Federated Search!'
