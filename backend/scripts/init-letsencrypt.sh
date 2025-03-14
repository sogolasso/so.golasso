#!/bin/bash

domains=(sogolassos.me www.sogolassos.me)
rsa_key_size=4096
data_path="./certbot"
email="your-email@example.com" # Change this to your email

# Make sure directories exist
mkdir -p "$data_path/conf/live/$domains"
mkdir -p "$data_path/www"

# Create dummy certificates
openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
  -keyout "$data_path/conf/live/$domains/privkey.pem" \
  -out "$data_path/conf/live/$domains/fullchain.pem" \
  -subj "/CN=localhost"

# Start nginx
docker-compose up --force-recreate -d nginx

# Delete dummy certificates
rm -Rf "$data_path/conf/live/$domains"

# Request Let's Encrypt certificate
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $email \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

# Reload nginx
docker-compose exec nginx nginx -s reload 