# POLDER Federated Search

## A federated search app for and by the polar data community
The POLDER Federated Search was originally developed by the [World Data System International Technology Office](https://wds-ito.org/) between 2021-2023 in response to needs identified by the [POLDER Working Group](http://polder.info). It is currently deployed at https://search.polder.info.

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
- Repositories in the [Canadian Consortium for Arctic Data Interoperability (CCADI)](https://ccadi.ca/) network:
  - [Polar Data Catalogue](http://polardata.ca)
  - [Nordicana D](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx)
  - Committee on earth observing satellites ([CEOS](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx))
  - Arctic Science and Technology Information System ([ASTIS](https://www.cen.ulaval.ca/nordicanad/en_BDDescription.aspx))
  - [ArcticConnect](https://arcticconnect.ca/)
  - Arctic Spatial Data Infrastructure ([ASDI](https://arctic-sdi.org/))
  - [INTERACT](https://eu-interact.org/)
  - Canadian Watershed Information Network ([CWIN](https://dev.uni-manitoba.links.com.au/data/dataset/))


#### Future work
- [National Snow and Ice Data Center](https://nsidc.org])
- CRITTERBASE
- Polar data from [DataStream](https://gordonfoundation.ca/initiatives/datastream/)


### Architecture
This tool uses Docker images to manage the different services that it depends on. One of those is [Gleaner](https://gleaner.io).

The web app itself that hosts the UI and does the searches is built using [Flask](https://flask.palletsprojects.com), which is a Python web framework. I chose Python because Python has good support for RDF and SPARQL operations with [RDFLib](https://rdflib.dev/). The frontend dependencies are HTML, JavaScript and SCSS, built using [Parcel](https://parceljs.org/). The maps in the user interface are built using [OpenLayers](https://openlayers.org/).

Errors in deployed versions of this project are collected with [Sentry](https://polder-federated-search.sentry.io/issues/?project=6247623).

### Deployment
A pre-built image for the web app is on Docker Hub as [wdsito/polder-federated-search](https://hub.docker.com/repository/docker/wdsito/polder-federated-search), and that is what all of the Helm/Kubernetes and Docker files in this repository are referencing. If you want to modify this project and build your own ones, you're welcome to.

There is also a sitemap-building step for some of the data repositories that don't have sitemaps that work in the way we want (e.g. they don't have sitemaps, we wanted to scope down the datasets crawled to just polar data, or some other reason). That step uses a purpose-built Docker image, and the code for that is in `build-sitemap` in this repository.

#### Images and versions
Images are automatically built with [Github Actions](https://github.com/POLDER-Crew/polder-federated-search/tree/main/.github/workflows), and tagged with the version specified in `package.json` (in this directory).

#### Deployment-support
There is a directory called `deployment-support`, which has files that both Docker and Helm / Kubernetes can use to configure Gleaner and Graphdb.

##### Gleaner
`docker.yaml` is what Docker uses to configure Gleaner when you run it using `docker compose`. Logs will go into this folder as well as other files associated with a Gleaner run.

##### GraphDB
Files in here are used by both Docker and Helm / Kubernetes to work with GraphDB. There are shell scripts to set up, clear, and write to GraphDB, as well as various settings files.

The file `EXAMPLE-graphdb-users.js` is standing in for a file that you should not check into source control - `graphdb-users.js`. The reason to not check it in is because it contains password hashes. You can either generate `bcrypt`-ed password hashes using a tool like [this one](https://bcrypt.online/) or start a GraphDB instance, create the users you want (remember to reset the admin password too, it's 'root' by default), and then download the `users.js` file, which is at ` /opt/graphdb/home/data/users.js`. You could use the GraphDB image referenced in `docker-compose.yaml` for this purpose. I recommend doing the following:
1. `docker run -p 127.0.0.1:7200:7200 -t ontotext/graphdb:10.2.0` (substitute the appropriate image version there)
1. Go to http://localhost:7200/users, change the admin password and add the users you want
1. Find the image running in Docker Desktop, go to the terminal tab and do `cat /opt/graphdb/home/data/users.js`
1. Congratulations, that's your new graphdb-users.js file.

Don't forget to set the matching passwords in your `.env` file as well.

The [GraphDB documentation](https://graphdb.ontotext.com/documentation/10.2/) may be of use to you here.

#### Docker
Assuming that you're starting from **this directory**:
1. To build and run the web app, Docker needs to know about some environment variables. There are examples ones in `dev.env` - copy it to `.env` and fill in the correct values for you. Save the file and then run `source .env`.
1. Install [Docker](https://docker.com)
   1. Also, For windows, click [here](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi) to install the WSL 2 (Windows Subsystem for Linux, version 2)
1. `cd docker`
1. `docker-compose up -d`
1. `docker-compose --profile setup up -d` in order to start all of the necessary services and set up Gleaner for indexing.
1. Do a crawl (these instructions assume you are in the `docker` directory): `docker-compose --profile crawl up -d`
1. When the crawl is done, write the data to the triplestore: `docker-compose --profile write up -d`
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
      graphdbIndexerPassword: <your base64 encoded value here>
      graphdbRootPassword: <your base64 encoded value here>
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

#### Testing your deployment
Go to the site and do a search for something like "Greenland", "ice" or "penguin" - those each have lots of results from both DataONE and the triplestore.
If you open a web inspector on the results, you can look for web elements with `class="result"`. POLDER-crawled results have a `data-source` attribute that’s set to `Gleaner`, and DataONE results have `data-source="DataONE"`. If you have both types, congratulations! You have a working federated search.

### Development
I'd love for people to use this for all kinds of scientific data repository searches - please feel free to fork it, submit a PR, or ask questions. The [Customization](https://polder-crew.github.io/Federated-Search-Documentation/customization.html) section of the book will be particularly useful to you.

If you use the Github Actions (see the Images and Versions section above) to automatically build and push Docker images to the WDS-ITO Docker hub, you'll need to update the versions in `package.json`, as well as `helm/Chart.yaml` and the versions in `docker/docker-compose.yaml` in order to get the images with your latest code.

#### Building
To build the Docker image for the web app, run `docker image build . `. For multi-architecture support, run `docker buildx build --no-cache --pull --platform=linux/arm64,linux/amd64 .`.

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

There are also some special map styles, in `app/static/maps`; you can read more about how they work in that directory.

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
