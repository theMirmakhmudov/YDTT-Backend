#!/bin/bash
set -e

# Arguments
GITHUB_TOKEN=$1
GITHUB_ACTOR=$2
DOMAIN=$3
SSL_EMAIL=$4

echo "🚀 Starting Deployment..."

# 1. Docker Login
echo "🔑 Logging into Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

# 2. Pull latest images
echo "⬇️ Pulling latest images..."
docker-compose pull

# 3. Stop old containers (optional, usually up -d handles recreation)
# docker-compose down

# 4. Start new containers
echo "🔥 Starting services..."
docker-compose up -d --remove-orphans

# 5. Prune old images to save space
echo "🧹 Cleaning up..."
docker image prune -f

echo "✅ Deployment Complete! App running on http://$DOMAIN"
