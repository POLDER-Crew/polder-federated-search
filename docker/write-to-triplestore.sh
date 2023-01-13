#! /bin/bash

token=$(curl -X POST -i -H 'Content-type: application/json' -d '{
     "username": "indexer-user",
     "password": "indexer-user"
}' 'http://localhost:9999/rest/login' | awk 'BEGIN {FS=": "}/^Authorization/{gsub(/\r/,"",$0); print $2}')

mc config host add minio http://localhost:9000
for i in $(mc find minio/gleaner/milled); do
  mc cat $i | curl -X POST -H "Authorization:$token" -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- 'http://localhost:9999/repositories/polder/statements'
done
