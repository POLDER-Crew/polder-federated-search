# POLDER Federated Search

## A federated search app for and by the polar data community

For more comprehensive documentation, [see this book](https://polder-crew.github.io/Federated-Search-Documentation).

### Covered data repositories
There are two ways a repository is included in searches that are made from this application- if the repository is indexed DataONE (and has data within the search parameters), and if the repository is indexed by the app itself.

#### DataONE Repositories
There are many DataONE repositories, but of particular interest to the polar research community are:
- [Arctic Data Center]( https://arcticdata.io/)
- [Netherlands Polar Data Center](https://npdc.nl)
- [BCO-DMO](https://www.bco-dmo.org/)
- [U.S. Antarctic Program Data Center](https://usap-dc.org)


#### Repositories indexed by this app
- [Greenland Ecosystem Monitoring](https://g-e-m.dk/)
- [British Antarctic Survey](https://www.bas.ac.uk/), via DataCite's GraphQL API (see `docker/build-bas-sitemap.sh` for how that works)
- [CLIVAR and Carbon Hydrographic Data Office (CCHDO)](https://cchdo.ucsd.edu/)
- Selected polar repositories in Nasa's [Global Change Master Directory (GCMD)](https://earthdata.nasa.gov)
    - [Australian Antarctic Data Centre](https://data.aad.gov.au/))
    - [World Glacier Monitoring Service (WGMS)](https://wgms.ch/)
    - [NOAA National Centers for Environmental Information (NCEI)](https://www.ncei.noaa.gov/)
    - [NASA Distributed Active Archive Center at the National Snow and Ice Data Center (NSIDC DAAC)](https://nsidc.org/daac/)
    - [Alaska Satellite Facility](https://asf.alaska.edu/)
    - [Norwegian Marine Data Centre (NMDC)](https://nmdc.no/nmdc)
    - [Permanent Service for Mean Sea Level (PSMSL)](https://psmsl.org/)
    - [World Data Centre for Geomagnetism, Edinburgh](http://www.wdc.bgs.ac.uk/)
    - [World Data Center for Solid Earth Physics](http://www.wdcb.ru/)


#### Future work
- [National Snow and Ice Data Center](https://nsidc.org])
- CRITTERBASE
- Repositories in the [Canadian Consortium for Arctic Data Interoperability (CCADI)](https://ccadi.ca/) network:
  - [Polar Data Catalogue](http://polardata.ca)
  - [Nordicana D](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx)
  - Committee on earth observing satellites ([CEOS](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx))
  - Arctic Science and Technology Information System ([ASTIS](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx))
  - [ArcticConnect](https://arcticconnect.ca/)
  - Arctic Spatial Data Infrastructure ([ASDI](https://arctic-sdi.org/))
  - [INTERACT](https://eu-interact.org/)
  - Canadian Watershed Information Network ([CWIN](https://dev.uni-manitoba.links.com.au/data/dataset/))


### Architecture
This tool uses Docker images to manage the different services that it depends on. One of those is [Gleaner](https://gleaner.io).

The web app itself that hosts the UI and does the searches is built using [Flask](https://flask.palletsprojects.com), which is a Python web framework. I chose Python because Python has good support for RDF and SPARQL operations with [RDFLib](https://rdflib.dev/). The frontend dependencies are HTML, JavaScript and SCSS, built using [Parcel](https://parceljs.org/).

### Deployment
A pre-built image for the web app is on Docker Hub as [nein09/polder-federated-search](https://hub.docker.com/repository/docker/nein09/polder-federated-search), and that is what all of the Helm/Kubernetes and Docker files in this repository are referencing. If you want to modify this project and build your own ones, you're welcome to.

#### Docker
Assuming that you're starting from **this directory**:
1. To build and run the web app, Docker needs to know about some environment variables. There are examples ones in `dev.env` - copy it to `.env` and fill in the correct values for you. Save the file and then run `source .env`.
1. Install [Docker](https://docker.com)
   1. Also, For windows, click [here](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi) to install the WSL 2 (Windows Subsystem for Linux, version 2)
1. `cd docker`
1. `docker-compose up -d`
1. `docker-compose --profile setup up -d` in order to start all of the necessary services and set up Gleaner for indexing.
1. Do a crawl (these instructions assume you are in the `docker` directory):
    1. `curl -O https://schema.org/version/latest/schemaorg-current-https.jsonld`
    1. `docker-compose --profile crawl up -d`

    NOTE: There is a missing step here. The crawled results need to be written to the triplestore. For now, you can run `./write-to-triplestore.sh`.
         1. For windows, you need to download [Cygwin](https://www.cygwin.com/setup-x86_64.exe).
         1. Change directory to the docker in Cygwin (`cd docker`).
         1. Run the `./write-to-triplestore.sh`. to write to triplestore.
1. Run the web app: `docker-compose --profile web up -d`

If you're using Docker Desktop, you can use the UI to open the docker-webapp image in a browser.

If you ever need to remove everything from the triplestore and start over, you can run `./clear-triplestore.sh`.


#### Helm/Kubernetes
1. Install helm (on OS X, something like `brew install helm`), or visit the [Helm website](http://helm.sh) for instructions.
1. This Helm chart uses an ingress controller. If you are running it in your own environment (like on your own dev machine), you need to install it like this
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
      sentryDsn: <your base64 encoded value here>
```
You can see that the values of the secrets are base64 encoded - in order to do this, run ` echo -n 'mysecretkey' | base64` on your command line for each value, and paste the result in where the key goes. Don't check in your real secrets anywhere!
  You can read more about secrets [here](https://kubernetes.io/docs/concepts/configuration/secret/).

In order to deploy to the `dev` or `prod` clusters, which are currently hosted in DataONE's analagous Kubernetes clusters, you need to ask someone in that organization for their Kubernetes config information. Name that file `polder.config` and put it in this directory; it'll get added to your environment automatically.

Assuming that you're starting from **this directory**, you can run:
```helm install polder ./helm -f helm/values-local.yaml```
to deploy a cluster to a docker-desktop Kubernetes instance.

Some notes: the `polder` can be replaced with whatever you want. For a dev or prod environment deploy, you need to first be using the correct Kubernetes context (`kubectl get-contexts` can tell you which ones are available to you). For dev, use `values-dev.yaml` instead of `values-local.yaml` and for a production deploy, use `values-prod.yaml`. Note that `values-dev` and `values-prod` are currently set up to deploy in DataONE's dev and prod Kubernetes clusters. They will not work without the correct keys and permissions from DataONE.

The cluster will take a few minutes to spin up. In addition to downloading all these Docker images and starting the web app, it does the following:
1. Starts a GraphDB Triplestore and creates a repository in it
1. Starts a Minio / S3 storage system
1. Initializes Gleaner
1. Kicks off a Gleaner index of the data repositories we want to get from there
1. Writes the resulting indexed metadata to GraphDB so we can search it

If you're using Docker desktop for all this, you can visit [http://localhost](http://localhost) and see it running!

The Helm chart also includes a Kubernetes `CronJob` that tells Gleaner to index [once a week](https://cron.help/#0_0_*_*_3). You can see it at `helm/templates/crawl.yaml`.

In addition, there's a `CronJob` that is set to run on the 30th of February, at `helm/templates/recreate-index.yaml`. This is a terrible hack to get around the fact that you cannot include a job in a Helm chart without it being automatically run when you deploy the chart. I wanted a way to remove all of the indexed files and recreate the triplestore without having to do a bunch of manual steps. In order to run this job, you can do `kubectl create job --from=cronjob/recreate-index reindex` - but do note that it will delete and recreate the entire index.

Note that the 30th of February has happened at least [twice](https://www.timeanddate.com/date/february-30.html), but given the other circumstances under which it occurred, I'm guessing that a federated search reindex will be the least of your worries.

Take a look at `helm/values-*.yaml` to customize this setup. Pay particular attention to `persistence` at the bottom; if you're running locally, you probably want `existing: false` in there.

### Related Docker images
A few of the setup and maintenence steps for the Polder Federated Search App require purpose-built Docker images. They can be found at:
- `build-sitemap` in this repository
- https://github.com/nein09/graphdb-docker

### Development
I'd love for people to use this for all kinds of scientific data repository searches - please feel free to fork it, submit a PR, or ask questions. The [Customization](https://polder-crew.github.io/Federated-Search-Documentation/customization.html) section of the book will be particularly useful to you.

#### Building
To build the Docker image for the web app, run `docker image build . `.

#### Setup
Assuming that you're starting from **this directory**:

The easiest setup for development on the web app itself is to use docker-compose for the dependencies, like Gleaner and GraphDB (`docker-compose up -d`), and run the app itself directly in Flask. To do that, follow the steps in the Deployment -> Docker section above, but skip the last one. Instead, do:
1. `cd ../` (to get back to **this directory**)
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `npm install --global yarn` (assuming you do not have yarn installed)
1.  `yarn install`
1.  `yarn watch` (assuming that you want to make JavaScript or CSS changes - if not, `yarn build` will do)
1.  `flask run`

You should see Flask's startup message, and get an address for your locally running web app.

#### Using Blazegraph instead of GraphDB
This project originally used Blazegraph instead of GraphDB. We changed because we wanted GraphDB's GeoSPARQL support and nice development console - but GraphDB is not open source, although a free version is available. If you wish to build a project that only has open-source software in it, you can use Blazegraph instead. See https://polder-crew.github.io/Federated-Search-Documentation/blazegraph.html for detailed instructions.

#### Standards and practices

##### Testing
This app includes Python unit tests! To run them from this directory, do `python -m unittest` after you activate your virtual environment.

Adding or updating tests as part of any contribution you make is strongly encouraged.

##### Styling
The SCSS styles are built assuming a mobile-first philosophy. Here are the breakpoints, for your convenience; they are also in `_constants.scss`.

- Small (default): up to 479px wide
- Medium: 480 - 767px wide
- Large: 768 - 1199px wide
- XLarge: 1200px and wider

#### Taking Performance Measurements

The file `docker_performance.ipynb` is meant to give you nifty graphs of the resources used by this app, broken out by docker container. You can use this method to look at the Kubernetes cluster performance too.

To set it up from **this directory**:
1. `source venv/bin/activate`
1. `pip install -r requirements-performance.txt`
1. Start your cluster using Docker or Helm
1. Use the `docker stats` command to write csv files like so: `while true; do docker stats --no-stream | cat >> ./`date -u +"%Y%m%d.csv"`; sleep 10; done`
1. Have the app do what you want to measure it doing (a setup and crawl, perhaps)
1. Start jupyter notebook by running `jupyter notebook` in this directory
1. Hit the Run button in the notebook, and you should see performance metrics. Depending on where you put the CSVs, you may need to change the code in the notebook a bit.
