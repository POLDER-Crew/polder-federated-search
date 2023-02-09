#! /bin/bash
# Get the security token to work with graphdb
token=$(curl -X POST -i -H 'Content-type: application/json' -d '{
     "username": "admin",
     "password": "root"
}' "$GRAPHDB_REST_URL"/login | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')
# Create the repository
curl -vs -X POST -H "Authorization:$token" -H 'Content-Type:multipart/form-data' -F "config=@./polder.ttl" "$GRAPHDB_REST_URL"/repositories
# Create the Lucene and geosparql connectors
curl -vs -X POST -H "Authorization:$token" -H 'Accept: application/json' --data-urlencode update@./lucene-connector.sparql "$GLEANER_ENDPOINT_URL"/statements
curl -vs -X POST -H "Authorization:$token" -H 'Accept: application/json' --data-urlencode update@./geosparql.sparql "$GLEANER_ENDPOINT_URL"/statements
# Turn on security and add a user that can write to the triplestore
curl -X POST -H "Authorization:$token" -H 'Content-Type: application/json' -d true "$GRAPHDB_REST_URL"/security

# Turn on read-only free access
curl -X POST -H "Authorization:$token" -H'Content-Type: application/json' -H 'Accept:  */*' -d '
    {
            "appSettings": {
                    "DEFAULT_SAMEAS": true,
                    "DEFAULT_INFERENCE": true,
                    "EXECUTE_COUNT": true,
                    "IGNORE_SHARED_QUERIES": true
                    },
            "authorities": ["string"],
            "enabled": true
    }' "$GRAPHDB_REST_URL"/security/free-access
