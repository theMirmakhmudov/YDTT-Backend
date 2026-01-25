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

CERT_FILE="./data/certbot/conf/live/$DOMAIN/fullchain.pem"
if [ ! -f "$CERT_FILE" ]; then
    echo "⚠️ SSL Certificates not found for $DOMAIN. Running initialization script..."
    echo "⏳ This may take a minute..."
    chmod +x init-letsencrypt.sh
    # Run in non-interactive mode (though script acts non-interactively if data dir missing)
    ./init-letsencrypt.sh
    echo "✅ SSL Initialization passed."
else
    echo "✅ SSL Certificates found. Skipping initialization."
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
