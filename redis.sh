#!/bin/bash

trap 'kill 0' EXIT

DIR=$(cd $(dirname "$0"); pwd)

ip=""
tmp=$(mktemp -d)
for i in $(seq 1 3); do
  work="$tmp/$i"
  mkdir -p "$work"
  cd "$work"
  echo "log: $work/log"
  PORT="700${i}" envsubst < $DIR/redis/redis.conf > "$work/redis.conf"

  redis-server "$work/redis.conf" >"$work/log" &
  ip="$ip localhost:700${i}"
done

sleep 1
redis-cli --cluster create $ip --cluster-replicas 0 --cluster-yes

wait
