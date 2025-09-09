#!/bin/bash
set -e

# Log in to ECR using instance role
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 260718839331.dkr.ecr.eu-west-1.amazonaws.com

echo "ECR login successful."
