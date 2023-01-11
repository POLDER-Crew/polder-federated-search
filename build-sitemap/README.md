This folder contains the necessary Dockerfile and script needed to query DataCite for DOIs associated with an organization, generate a sitemap from it, and place that sitemap in Minio, where Gleaner can then use it to crawl those DOIs, as if they were all on one website.

The docker image is currently published on Docker Hub as [wdsito/build-sitemap](https://hub.docker.com/r/wdsito/build-sitemap). It could be used to build other sitemaps as well. It contains an instance of Minio Client, curl, jq, and bash.

Build the image by doing `docker buildx build --no-cache --pull --platform=linux/arm64,linux/amd64 --push --tag wdsito/build-sitemap .`
