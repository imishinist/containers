#!/bin/bash

jsonl=$1

curl 'http://localhost:8983/solr/poc/update?commitWithin=1000&overwrite=true&wt=json' \
  -H 'Content-type: application/json' \
  --data @<(jq -rs '.' "$jsonl")
