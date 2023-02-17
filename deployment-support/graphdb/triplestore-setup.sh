#! /bin/bash
# Get the security token to work with graphdb
# Yup, this is the default root password. Not great.
token=$(curl -X POST -i -H 'Content-type: application/json' -d '{
     "username": "admin",
     "password": "root"
}' "$GRAPHDB_REST_URL"/login | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')
# Create the repository
curl -vs -X POST -H "Authorization:$token" -H 'Content-Type:multipart/form-data' -F "config=@./polder.ttl" "$GRAPHDB_REST_URL"/repositories
# Create the Lucene and geosparql connectors
curl -vs -X POST -H "Authorization:$token" -H 'Accept: application/json' --data-urlencode update@./lucene-connector.sparql "$GLEANER_ENDPOINT_URL"/statements
curl -vs -X POST -H "Authorization:$token" -H 'Accept: application/json' --data-urlencode update@./geosparql.sparql "$GLEANER_ENDPOINT_URL"/statements
# Add a user that can write to the triplestore
curl -vs -X POST -H "Authorization:$token" -H 'Content-Type: application/json' -d '
    {
        "appSettings": {
            "DEFAULT_SAMEAS": true,
            "DEFAULT_INFERENCE": true,
            "EXECUTE_COUNT": true,
            "IGNORE_SHARED_QUERIES": false
        },
        "grantedAuthorities": ["ROLE_USER","WRITE_REPO_*","READ_REPO_*"],
        "username": "'"$GRAPHDB_INDEXER_USER"'",
        "password": "'"$GRAPHDB_INDEXER_PASSWORD"'"
    }' "$GRAPHDB_REST_URL"/security/users/"$GRAPHDB_INDEXER_USER"
