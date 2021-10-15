# POLDER Federated Search

## A federated search app for and by the polar data community

### Covered data repositories
- [Arctic Data Center]( https://arcticdata.io/)
- [Netherlands Polar Data Center](https://npdc.nl)
- [BCO-DMO](https://www.bco-dmo.org/)
- Todo: If I'm doing global DataOne searches, what else might I cover?
- [Australian Antarctic Data Centre](https://data.aad.gov.au/)
- [National Snow and Ice Data Center](https://nsidc.org])

### Architecture
This tool uses docker to manage the different services that it depends on. One of those is [Gleaner](https://gleaner.io).

The web app itself that hosts the UI and does the searches is built using [Flask](https://flask.palletsprojects.com), which is a Python web framework. I chose Python because DataOne has [client libraries](https://dataone-python.readthedocs.io/en/latest/#python-libraries-for-software-developers) written in Python, and Python has good support for RDF and SPARQL operations with [RDFLib](https://rdflib.dev/).

### Deployment
Assuming that you're starting from **this directory**:
To build the Docker image for this app, run `docker build -f docker/Dockerfile . `. Then, you can run it using `docker run`.

#### Setup
Assuming that you're starting from **this directory**:

1. Install [Docker](https://docker.com)
1. `cd docker`
1. `docker-compose --profile setup up -d` in order to start all of the necessary services and set up Gleaner for indexing.

For development, you can do `flask run` from this directory, or follow the directions in the Deployment section above to run the app with Docker.

#### Doing a crawl
Assuming that you're starting from **this directory**:

1. `cd docker`
1. `curl -O https://schema.org/version/latest/schemaorg-current-https.jsonld`
1. `docker-compose --profile crawl up -d`

