#! /bin/bash

mc config host add minio http://localhost:9000
for i in $(mc find minio/gleaner/milled); do
  mc cat <(echo 'update=insert data {') $i <(echo '}') | curl -X POST -H 'Content-Type:application/sparql-update;charset=utf-8' -u "admin:admin" --data-binary @- 'http://localhost:9999/polder/update'
done
