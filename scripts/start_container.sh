#!/bin/bash
set -e

IMAGE_URI="260718839331.dkr.ecr.eu-west-1.amazonaws.com/bake-api:latest"
CONTAINER_NAME="bake-api"
PARAM_PATH="/bake-api/prod"
TEMP_ENV_FILE=$(mktemp)

echo "Fetching parameters from AWS Parameter Store..."

# Fetch all parameters under the specified path and format them into a .env file
aws ssm get-parameters-by-path --path "$PARAM_PATH" --with-decryption --query "Parameters" | \
jq -r '.[] | .Name + "=" + .Value' | \
sed "s#$PARAM_PATH/##" > "$TEMP_ENV_FILE"

echo "Pulling latest Docker image..."
docker pull $IMAGE_URI

echo "Starting new container with fetched environment variables..."
docker run -d -p 8000:8000 --name $CONTAINER_NAME --rm --env-file "$TEMP_ENV_FILE" $IMAGE_URI

# Clean up the temporary file
rm "$TEMP_ENV_FILE"

echo "Container started successfully."
exit 0