#!/bin/bash
echo "Stopping existing container if running..."
docker stop bake-api || true
docker rm bake-api || true
