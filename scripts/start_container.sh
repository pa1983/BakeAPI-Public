#!/bin/bash
set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_DEFAULT_REGION="eu-west-1"
REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/bake-api

echo "Pulling latest Docker image..."
docker pull $REPOSITORY_URI:latest

echo "Starting new container on port 8000..."
docker run -d --name bake-api -p 8000:8000 $REPOSITORY_URI:latest
