FROM golang:alpine3.15 as builder

LABEL maintainer="Melinda Minch"

ENV GOPATH /go
ENV CGO_ENABLED 0
ENV GO111MODULE on

RUN  \
     apk add --no-cache git && \
     git clone https://github.com/minio/mc && cd mc && \
     go install -v -ldflags "$(go run buildscripts/gen-ldflags.go)"

FROM alpine:3.15

ARG TARGETARCH

COPY --from=builder /go/bin/mc /usr/bin/mc
COPY --from=builder /go/mc/CREDITS /licenses/CREDITS
COPY --from=builder /go/mc/LICENSE /licenses/LICENSE

RUN  \
     apk update && \
     apk add ca-certificates curl jq bash python3 && \
     rm -rf /var/cache/apk/*

COPY build-sitemaps.sh /usr/local/bin/build-sitemaps.sh

RUN chmod +x /usr/local/bin/build-sitemaps.sh

ENTRYPOINT ["build-sitemaps.sh"]
