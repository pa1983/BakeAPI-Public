#!/bin/bash
set -e

IMAGE_URI="260718839331.dkr.ecr.eu-west-1.amazonaws.com/bake-api:latest"
CONTAINER_NAME="bake-api"
PARAM_PATH="/bake-api/prod"
TEMP_ENV_FILE=$(mktemp)

echo "Fetching parameters from AWS Parameter Store..."

# The application was set up with a .env file to hold the parameters, including secure items such as API keys
# These files should not be stored in version control for security reason, therefore the params are stored in
# aws ssm.  To make the application work in its current form, the ssm parameters are queried, pulled down as JSON,
# then reformatted into a standard .env file format.
aws ssm get-parameters-by-path --path "$PARAM_PATH" --with-decryption --query "Parameters" | \
jq -r '.[] | .Name + "=" + .Value' | \
sed "s#$PARAM_PATH/##" > "$TEMP_ENV_FILE"

echo "Pulling latest Docker image..."
docker pull $IMAGE_URI

echo "Starting new container with fetched environment variables..."
# echo "Temporarily removed  --rm from run config to leave container in place in case of error for debugging "
# pass the temp env file name into the docker command so application can find config parameters
docker run -d -p 8000:8000 --name --rm $CONTAINER_NAME --env-file "$TEMP_ENV_FILE" $IMAGE_URI
# the docker command runs the container in detached mode, exposing port 8000 inside the container on 8000 outside,
# it sets the container to be removed once it closes down, and gets its .env file from the temp file created above

# Clean up the temporary file to avoid future conflicts and prevent secure data being stored locally unnecessarily
rm "$TEMP_ENV_FILE"

echo "Container started successfully."
exit 0