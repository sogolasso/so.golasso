@echo off
echo Setting up staging environment...

REM Set environment variables
set DOMAIN=staging.sogolassos.me
set EMAIL=geral@sogolassos.me

REM Create necessary directories
mkdir certbot\conf certbot\www logs\nginx 2>nul

REM Create temporary nginx config
echo Creating temporary Nginx configuration...
(
echo server {
echo     listen 80;
echo     server_name staging.sogolassos.me;
echo.    
echo     location /.well-known/acme-challenge/ {
echo         root /var/www/certbot;
echo     }
echo.    
echo     location / {
echo         return 200 'OK';
echo         add_header Content-Type text/plain;
echo     }
echo }
) > nginx/staging-temp.conf

REM Start Nginx with temporary config
echo Starting Nginx with temporary configuration...
docker compose -f docker-compose.staging.yml up -d nginx

REM Wait for Nginx to start
timeout /t 5 /nobreak

REM Get SSL certificate
echo Obtaining SSL certificate...
docker compose -f docker-compose.staging.yml run --rm certbot certbot certonly --webroot --webroot-path /var/www/certbot --email %EMAIL% --agree-tos --no-eff-email -d %DOMAIN%

REM Replace temporary Nginx config
move /Y nginx\staging.sogolassos.me.conf nginx\staging-temp.conf

REM Start services
echo Starting staging environment...
docker compose -f docker-compose.staging.yml down
docker compose -f docker-compose.staging.yml up -d db redis

REM Wait for database
echo Waiting for database to be ready...
timeout /t 10 /nobreak

REM Run migrations
echo Running database migrations...
docker compose -f docker-compose.staging.yml run --rm web alembic upgrade head

REM Start all services
echo Starting all services...
docker compose -f docker-compose.staging.yml up -d

REM Run tests
echo Running tests...
docker compose -f docker-compose.staging.yml run --rm web pytest

echo.
echo Staging environment is ready!
echo Access the staging site at: https://staging.sogolassos.me
echo API endpoints: https://staging.sogolassos.me/api
echo Test endpoints: https://staging.sogolassos.me/test
echo.

REM Show logs
echo Showing logs (Ctrl+C to exit)...
docker compose -f docker-compose.staging.yml logs -f 