#!/bin/bash

# Set environment variables
export DOMAIN=staging.sogolassos.me
export EMAIL=your-email@example.com  # Change this

# Create necessary directories
mkdir -p certbot/conf certbot/www logs/nginx

# Create a temporary Nginx configuration for SSL setup
cat > nginx/staging-temp.conf << EOF
server {
    listen 80;
    server_name staging.sogolassos.me;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

# Start Nginx with temporary config
echo "Starting Nginx with temporary configuration..."
docker-compose -f docker-compose.staging.yml up -d nginx

# Wait for Nginx to start
sleep 5

# Get SSL certificate
echo "Obtaining SSL certificate..."
docker-compose -f docker-compose.staging.yml run --rm certbot certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d staging.sogolassos.me

# Replace temporary Nginx config with full config
mv nginx/staging.sogolassos.me.conf nginx/staging-temp.conf

# Start all services
echo "Starting staging environment..."
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d db redis
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.staging.yml run --rm web alembic upgrade head

# Start all services
echo "Starting all services..."
docker-compose -f docker-compose.staging.yml up -d

# Run tests
echo "Running tests..."
docker-compose -f docker-compose.staging.yml run --rm web pytest

echo "Staging environment is ready!"
echo "Access the staging site at: https://staging.sogolassos.me"
echo "API endpoints: https://staging.sogolassos.me/api"
echo "Test endpoints: https://staging.sogolassos.me/test"

# Show logs
echo "Showing logs (Ctrl+C to exit)..."
docker-compose -f docker-compose.staging.yml logs -f 