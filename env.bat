: :# A starter, sample env file, for local development. Copy this to .env and fill in real values.

: : # Flask settings
set FLASK_APP=main.py
set FLASK_RUN_HOST=0.0.0.0
set SECRET_KEY= “whatever you want”
: : # Server will reload itself on file changes if in dev mode
set FLASK_ENV=development

: : # Setup for Sentry, our error tracking software
set SENTRY_DSN=

: : # If you are using docker-compose to run the other services, and flask run for development
set GLEANER_ENDPOINT_URL=http://localhost:9999/blazegraph/namespace/polder/sparql

: : # Object store keys
set MINIO_ACCESS_KEY= "hello"
set MINIO_SECRET_KEY="hello"

: : # local data volumes
set GLEANER_BASE=/tmp/gleaner/
set GLEANER_OBJECTS=${GLEANER_BASE}/datavol/s3
set GLEANER_GRAPH=${GLEANER_BASE}/datavol/graph

: : # Kubernetes deployment helper
set KUBECONFIG=~/.kube/config:~/polder-federated-search/helm/polder.config
