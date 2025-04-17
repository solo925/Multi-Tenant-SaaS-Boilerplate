#!/bin/bash

echo "🚀 Starting local setup..."
docker compose -f devops/docker/docker-compose.yml up --build
