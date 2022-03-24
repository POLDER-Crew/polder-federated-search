#! /bin/bash

mc config host add minio http://localhost:9000
for i in $(mc find minio/gleaner/milled); do
  mc cat $i | curl -X POST -H 'Content-Type:text/x-nquads;charset=utf-8' --data-binary  @- http://localhost:9999/blazegraph/namespace/polder/sparql
done
