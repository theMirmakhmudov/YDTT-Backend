#!/bin/bash
set -e

# Load environment variables from .env
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

# Parameters
domains="${DOMAIN}" # Using env var from shell
rsa_key_size=4096
data_path="./data/certbot"
email="${SSL_EMAIL}" # Using env var from shell
staging=0 # Set to 1 if you're testing your setup to avoid hitting request limits

# Automatic execution: We assume if this script is run, we want to regenerate/init.
# Removing interactive check for CI/CD compatibility.
# if [ -d "$data_path" ]; then ... fi

if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

echo "### Ensuring permissions for webroot ..."
mkdir -p "$data_path/www"
# Note: Skip chmod as directory may be owned by root from Docker containers

echo "### Creating dummy certificate for $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo


echo "### Starting nginx ..."
docker compose up --force-recreate -d nginx
echo "### Waiting for Nginx to fully start..."
sleep 10

echo "### DIAGNOSTIC: Testing Nginx configuration locally..."
mkdir -p "$data_path/www/.well-known/acme-challenge"
echo "success" > "$data_path/www/.well-known/acme-challenge/test-challenge.txt"
chmod 644 "$data_path/www/.well-known/acme-challenge/test-challenge.txt"

echo "Attempting to fetch test file internally..."
# Use docker exec to curl from inside the nginx container (or app container) simply to test routing
# Since nginx container minimal, we use curl from host against localhost:80
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: ${domains}" http://localhost/.well-known/acme-challenge/test-challenge.txt)

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ Diagnostic Passed: Nginx is serving challenge files correctly."
else
    echo "❌ Diagnostic Failed: Local test returned HTTP $HTTP_STATUS"
    
    echo "--- DEBUG START ---"
    echo "1. Verifying file inside container..."
    docker compose exec nginx ls -la /var/www/certbot/.well-known/acme-challenge/test-challenge.txt || echo "FILE NOT FOUND IN CONTAINER"
    
    echo "2. Checking Nginx Configuration (Envsubst result)..."
    docker compose exec nginx nginx -T | grep -A 10 "server_name"
    
    echo "3. Nginx Error Log (Last 5 lines)..."
    docker compose exec nginx tail -n 5 /var/log/nginx/error.log
    echo "--- DEBUG END ---"
    
    echo "Skipping Certbot to avoid rate limits until fixed."
    exit 1
fi



echo "### Deleting dummy certificate for $domains ..."
docker compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/live/${domains}-0001 && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/archive/${domains}-0001 && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf && \
  rm -Rf /etc/letsencrypt/renewal/${domains}-0001.conf" certbot
echo


echo "### Requesting Let's Encrypt certificate for $domains ..."
#Join $domains to -d args
domain_args=""
for domain in "${domains}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="-m $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### Reloading nginx ..."
docker compose exec nginx nginx -s reload
