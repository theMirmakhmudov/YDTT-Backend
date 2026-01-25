#!/bin/bash
# One-time script to fix SSL certificate path issue
# Run this on the server to remove old certificates and re-initialize

set -e

echo "🧹 Cleaning up old SSL certificates..."

# Stop nginx to release certificate files
docker compose stop nginx

# Remove all certificate directories (including -0001 variants)
docker compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/* && \
  rm -Rf /etc/letsencrypt/archive/* && \
  rm -Rf /etc/letsencrypt/renewal/*" certbot

echo "✅ Old certificates removed"
echo "🔄 Re-running SSL initialization..."

# Re-run the SSL initialization script
./init-letsencrypt.sh

echo "✅ SSL certificates fixed!"
echo "🚀 Restarting all services..."

# Restart all services
docker compose up -d

echo "✅ Done! Check https://your-domain.com"
