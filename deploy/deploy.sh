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
docker compose pull

# 3. Stop old containers (optional, usually up -d handles recreation)
# docker compose down

# 4. Preparing Configuration
echo "⚙️  Generating Nginx configuration..."
# Manually substitute environment variables using sed to avoid Docker template issues
# We use | as delimiter to handle potential slashes in variables safely
sed -e "s|\${API_DOMAIN}|${DOMAIN}|g" \
    nginx.conf > nginx.final.conf

# 5. Stop and remove old containers cleanly
echo "🛑 Stopping old containers..."
docker compose down --remove-orphans

# Force remove any orphaned nginx container (from previous failed deployments)
echo "🧹 Cleaning up orphaned containers..."
docker rm -f ydtt-nginx 2>/dev/null || true

# 6. Start new containers
echo "🔥 Starting services..."
docker compose up -d --remove-orphans

# 5. Check for SSL Certificates & Initialize if missing (First Run Automation)
if [ ! -d "./data/certbot" ]; then
    echo "📁 Creating certbot data directory..."
    mkdir -p ./data/certbot/conf ./data/certbot/www
    chmod -R 755 ./data/certbot
fi

# Check if ANY certificate exists for this domain (check inside Docker volume)
echo "🔍 Checking for existing SSL certificates..."
CERT_EXISTS=$(docker compose run --rm --entrypoint "sh -c 'ls -d /etc/letsencrypt/live/${DOMAIN}* 2>/dev/null || true'" certbot)

if [ -z "$CERT_EXISTS" ]; then
    echo "⚠️ SSL Certificates not found for $DOMAIN. Running initialization script..."
    echo "⏳ This may take a minute..."
    chmod +x init-letsencrypt.sh
    ./init-letsencrypt.sh
    echo "✅ SSL Initialization passed."
else
    echo "✅ SSL Certificates found: $CERT_EXISTS"
    echo "Skipping SSL initialization (reusing existing certificate)."
    
    # Extract just the directory name (e.g., "api.ydtt.uz-0001")
    CERT_DIR=$(echo "$CERT_EXISTS" | xargs basename)
    echo "📝 Certificate directory: $CERT_DIR"
    
    # Update nginx config to use the actual certificate path
    if [ "$CERT_DIR" != "$DOMAIN" ]; then
        echo "📝 Updating nginx to use certificate: $CERT_DIR"
        sed -i "s|/etc/letsencrypt/live/\${API_DOMAIN}|/etc/letsencrypt/live/$CERT_DIR|g" nginx.final.conf
    fi
fi

# 6. Run Database Migrations
echo "📊 Running database migrations..."
docker compose exec -T app alembic upgrade head

# 7. Create Initial Superuser
echo "👤 Creating initial superuser (if needed)..."
docker compose exec -T app python -m app.initial_data

# 8. Prune old images to save space
echo "🧹 Cleaning up..."
docker image prune -f

echo "✅ Deployment Complete! App running on http://$DOMAIN"
