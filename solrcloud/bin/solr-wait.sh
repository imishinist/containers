#!/bin/bash

while true; do
  status=$(curl -s --retry 3 --connect-timeout 500 -o /dev/null -w '%{http_code}' http://127.0.0.1:8983/solr/)
  [[ "000" == "$status" ]] && echo "WARN: http connection error" && sleep 2 && continue
  [[ "200" == "$status" ]] && break
  echo "ERROR: return http status ${status}"
  exit 1
done
