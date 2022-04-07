#! /bin/bash

mc config host add minio http://localhost:9000
for i in $(mc find minio/gleaner/milled); do
  mc cat $i | curl -X POST -H 'Content-Type:text/rdf+n3;charset=utf-8' --data-binary  @- http://localhost:9999/bigdata/namespace/polder/sparql
done
