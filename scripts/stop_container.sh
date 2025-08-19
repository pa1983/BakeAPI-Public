#!/bin/bash
set -e

CONTAINER_NAME="bake-api"

# Check if any container with that name exists (running or stopped  -a flag).
if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Found container ${CONTAINER_NAME}. Stopping and removing it."

    # Stop the container if it is running
    if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
        docker stop ${CONTAINER_NAME}
    fi

    # Remove the container
    docker rm ${CONTAINER_NAME}
else
    echo "Container ${CONTAINER_NAME} not found. Nothing to do."
fi

exit 0