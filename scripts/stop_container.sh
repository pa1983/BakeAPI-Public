#!/bin/bash

CONTAINER_NAME="bake-api"

# Use docker ps -q to check if a container with that name is running.
# The output will be a container ID if it exists, or empty if it doesn't.
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Found running container ${CONTAINER_NAME}. Stopping and removing it."
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
else
    echo "Container ${CONTAINER_NAME} not found. Nothing to do."
fi

# Optional: Prune old, unused images to save disk space
docker image prune -a -f

exit 0 # Always exit with a success code