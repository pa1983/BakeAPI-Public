#!/bin/bash
set -e

REPO_URI="260718839331.dkr.ecr.eu-west-1.amazonaws.com/bake-api"
IMAGE_TAG="latest"
CONTAINER_NAME="bake-api"
PORT="8000"

echo "Stopping existing container (if any)..."
docker stop $CONTAINER_NAME || true
docker rm $CONTAINER_NAME || true

echo "Pulling Docker image $REPO_URI:$IMAGE_TAG..."
docker pull $REPO_URI:$IMAGE_TAG

echo "Starting new container..."
docker run -d --name $CONTAINER_NAME -p $PORT:$PORT $REPO_URI:$IMAGE_TAG

echo "Container $CONTAINER_NAME started on port $PORT."
