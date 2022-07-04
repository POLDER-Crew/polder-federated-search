#! /bin/bash
# Delete the repository
curl --get -X DELETE http://localhost:9999/rest/repositories/polder
# Create the repository
curl -X POST -H 'Content-Type:multipart/form-data' -F "config=@./polder.ttl" http://localhost:9999/rest/repositories
# Recreate Lucene and geosparql connectors
curl -X POST --header 'Accept: application/json' --data-urlencode update@./lucene-connector.sparql http://localhost:9999/repositories/polder/statements
curl -X POST --header 'Accept: application/json' --data-urlencode update@./geosparql.sparql http://localhost:9999/repositories/polder/statements
