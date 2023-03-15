#! /bin/bash
# Get a security token so we can work with Graphdb in this way
token=$(curl -X POST -i -H 'Content-type: application/json' -d '{
     "username": "admin",
     "password": "'"$GRAPHDB_ROOT_PASSWORD"'"
}' "$GRAPHDB_REST_URL"/login | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')

# # Delete the repository
curl -X GET -H "Authorization:$token" -X DELETE "$GRAPHDB_REST_URL"/repositories/polder
# Create the repository
curl -X POST -H "Authorization:$token" -H 'Content-Type:multipart/form-data' -F "config=@./polder.ttl" "$GRAPHDB_REST_URL"/repositories
# # Create the Lucene and geosparql connectors
curl -vs -X POST -H 'Accept: application/json' -H "Authorization:$token" --data-urlencode update@./lucene-connector.sparql "$GLEANER_ENDPOINT_URL"/statements
curl -vs -X POST -H 'Accept: application/json' -H "Authorization:$token" --data-urlencode update@./geosparql.sparql "$GLEANER_ENDPOINT_URL"/statements
