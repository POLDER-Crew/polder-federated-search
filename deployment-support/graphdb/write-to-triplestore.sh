#! /bin/bash
mc config host add minio "$MINIO_SERVER_HOST":"$MINIO_SERVER_PORT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"

token=$(curl -X POST -i -H "X-GraphDB-Password: $GRAPHDB_INDEXER_PASSWORD" -H 'Content-type: application/json' "$GRAPHDB_REST_URL"/login/"$GRAPHDB_INDEXER_USER" | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')

for i in $(mc find minio/"$STORAGE_BUCKET"/milled); do
  # Get the security token to work with graphdb
  status=$(mc cat $i | curl -o /dev/null -s -w '%{http_code}' -X POST -H "Authorization:$token" -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- "$GLEANER_ENDPOINT_URL"/statements)
  # status 000 often leads to subsequent 401, which is why these statements are in this order.
  if [ "$status" = "000" ]
  then
    while [ "$status" = "000" ]
    do
      echo "failed to connect to minio. Retrying in 10 seconds..."
      sleep 10
      status=$(mc cat $i | curl -s -w '%{http_code}' -X POST -H "Authorization:$token" -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- "$GLEANER_ENDPOINT_URL"/statements)
    done
  fi
  if [ "$status" = "401" ]
  then
    echo "Authentication failed while writing." $i "Fetching new token and retrying."
    token=$(curl -X POST -i -H "X-GraphDB-Password: $GRAPHDB_INDEXER_PASSWORD" -H 'Content-type: application/json' "$GRAPHDB_REST_URL"/login/"$GRAPHDB_INDEXER_USER" | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')
    status=$(mc cat $i | curl -s -w '%{http_code}' -X POST -H "Authorization:$token" -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- "$GLEANER_ENDPOINT_URL"/statements)
  fi
  echo "RDF upload status for" $i ":" $status

done
