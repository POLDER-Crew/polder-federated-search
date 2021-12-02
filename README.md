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
This tool uses Docker images to manage the different services that it depends on. One of those is [Gleaner](https://gleaner.io).

The web app itself that hosts the UI and does the searches is built using [Flask](https://flask.palletsprojects.com), which is a Python web framework. I chose Python because Python has good support for RDF and SPARQL operations with [RDFLib](https://rdflib.dev/).

### Deployment
A pre-built image for the web app is on Docker Hub as [nein09/polder-federated-search](https://hub.docker.com/repository/docker/nein09/polder-federated-search), and that is what all of the Helm/Kubernetes and Docker files in this repository are referencing. If you want to modify this project and build your own ones, you're welcome to.

#### Docker
Assuming that you're starting from **this directory**:
1. To build and run the web app, Docker needs to know about some environment variables. There are examples ones in `dev.env` - copy it to `.env` and fill in the correct values for you. Save the file and then run `source .env`.
1. Install [Docker](https://docker.com)
1. `cd docker`
1. `docker-compose up -d`
1. Go to your [local Blazegraph instance](http://localhost:9999/blazegraph/#namespaces) and add a new namespace - this is because the default one does not come with a full text index. Name it `polder` (or whatever you want, but you will need to change the GLEANER_ENDPOINT_URL environment variable if you don't name it that). Select 'quads' in the mode dropdown menu, and check the text boxes after "Full text index" and "Enable geospatial".
1. If you want to try queries out on Blazegraph directly, be sure to click 'Use' next to your new namespace after you create it.
1. `docker-compose --profile setup up -d` in order to start all of the necessary services and set up Gleaner for indexing.
1. Do a crawl (these instructions assume you are in the `docker` directory):
    1. `curl -O https://schema.org/version/latest/schemaorg-current-https.jsonld`
    1. `docker-compose --profile crawl up -d
    NOTE: There is a missing step here. The crawled results need to be written to the triplestore. For now, you can run `./write-to-triplestore.sh`.
1. Run the web app: `docker-compose --profile web up -d`

If you're using Docker Desktop, you can use the UI to open the docker-webapp image in a browser.


#### Helm/Kubernetes

1. Install helm (on OS X, something like `brew install helm`), or visit the [Helm website](http://helm.sh) for instructions.
1. This Helm chart uses an ingress controller, which you need to install, like this:
    ```
        helm upgrade --install ingress-nginx ingress-nginx \
      --repo https://kubernetes.github.io/ingress-nginx \
      --namespace ingress-nginx --create-namespace
    ```
    You may need some additional steps for minikube or MicroK8s - see the [ingress-nginx documentation](https://kubernetes.github.io/ingress-nginx/deploy/#environment-specific-instructions) for more details.
1. This app needs some secrets to run. Inside `helm/templates`, create a file named `secrets.yaml`. It's listed in `.gitignore`, so it won't get checked in.
That file will be structured like this:

```
    apiVersion: v1
    kind: Secret
    metadata:
      name: {{ .Release.Name }}-secrets
    data:
      minioAccessKey: <your base64 encoded value here>
      minioSecretKey: <your base64 encoded value here>
      flaskSecretKey: <your base64 encoded value here>
```
You can see that the values of the secrets are base64 encoded - in order to do this, run ` echo -n 'mysecretkey' | base64` on your command line for each value, and paste the result in where the key goes. Don't check in your real secrets anywhere!
  You can read more about secrets [here](https://kubernetes.io/docs/concepts/configuration/secret/).
1. Assuming that you're starting from **this directory**, run `helm install polder ./helm` ; the `polder` can be replaced with whatever you want.
1. The cluster will take a few minutes to spin up. In addition to downloading all these Docker images and starting the web app, it does the following:
    1. Starts a Blazegraph Triplestore and creates a namespace in it
    1. Starts a Minio / S3 storage system
    1. Initializes Gleaner
    1. Kicks off a Gleaner index of the data repositories we want to get from there
    1. Writes the resulting indexed metadata to Blazegraph so we can search it
1. If you're using Docker desktop for all this, you can visit [http://localhost](http://localhost) and see it running!

The Helm chart also includes a Kubernetes `CronJob` that tells Gleaner to index [once a week](https://cron.help/#0_0_*_*_3).

### Development
I'd love for people to use this for all kinds of scientific data repository searches - please feel free to fork it, submit a PR, or ask questions.

#### Building
To build the Docker image for the web app, run `docker image build . `.

#### Setup
Assuming that you're starting from **this directory**:

The easiest setup for development on the web app itself is to use docker-compose for the dependencies, like Gleaner and Blazegraph, and run the app itself directly in Flask. To do that, follow the steps in the Deployment section under Docker, but skip the last one. Instead, do:
1. `cd ../` (to get back to **this directory**)
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `flask run`

You should see Flask's startup message, and get an address for your locally running web app.

