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

### Deployment

#### Setup
1. Install [Docker](https://docker.com)
1. You can then run `docker-compose --profile setup up -d` in order to start all of the necessary services and set up Gleaner for indexing.

#### Doing a crawl
1. `curl -O https://schema.org/version/latest/schemaorg-current-https.jsonld`
1. `docker-compose --profile crawl up -d`
