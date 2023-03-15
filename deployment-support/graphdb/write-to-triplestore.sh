#! /bin/bash
# Get the security token to work with graphdb
token=$(curl -X POST -i -H "X-GraphDB-Password: $GRAPHDB_INDEXER_PASSWORD" -H 'Content-type: application/json' "$GRAPHDB_REST_URL"/login/"$GRAPHDB_INDEXER_USER" | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')
mc config host add minio "$MINIO_SERVER_HOST":"$MINIO_SERVER_PORT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
for i in $(mc find minio/gleaner/milled); do
  mc cat $i | curl -X POST -H "Authorization:$token" -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- "$GLEANER_ENDPOINT_URL"/statements
done
