#!/bin/bash
# Pull the new image and start the container
# The IMAGE_URI is passed in automatically by CodeDeploy from the imagedefinitions.json file
docker pull $IMAGE_URI
docker run -d -p 8000:8000 --name my-bake-api $IMAGE_URI