#!/bin/bash

# Script to get SSL certificates for both api.ydtt.uz and admin.ydtt.uz
# This should be run ONCE manually on the server before deployment

set -e

# Configuration
DOMAIN1="api.ydtt.uz"
DOMAIN2="admin.ydtt.uz"
EMAIL="your-email@example.com"  # Change this to your email

echo "🔒 Obtaining SSL certificates for:"
echo "  - $DOMAIN1"
echo "  - $DOMAIN2"

# Create data directories
mkdir -p ./data/certbot/conf
mkdir -p ./data/certbot/www

# Download recommended TLS parameters
if [ ! -e "./data/certbot/conf/options-ssl-nginx.conf" ] || [ ! -e "./data/certbot/conf/ssl-dhparams.pem" ]; then
  echo "⬇️ Downloading recommended TLS parameters..."
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "./data/certbot/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "./data/certbot/conf/ssl-dhparams.pem"
fi

# Request certificate for BOTH domains in one cert
echo "📜 Requesting SSL certificate..."
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  -d $DOMAIN1 \
  -d $DOMAIN2

echo "✅ SSL certificates obtained!"
echo ""
echo "Certificate location: ./data/certbot/conf/live/$DOMAIN1/"
echo ""
echo "Now restart nginx:"
echo "  docker compose restart nginx"
