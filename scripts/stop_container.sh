#!/bin/bash
# Stop and remove the existing container if it exists
CONTAINER_ID=$(docker ps -qf "name=my-bake-api")
if [ -n "$CONTAINER_ID" ]; then
  docker stop $CONTAINER_ID
  docker rm $CONTAINER_ID
fi