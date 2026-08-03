#!/bin/bash
# Setup statt-tipex.de on Ubuntu 24.04 VPS
# Run as root: bash setup-statt-tipex.sh

set -e

DOMAIN="statt-tipex.de"
WEBROOT="/var/www/statt-tipex"

echo "=== statt-Tipex Setup ==="

# 1. Create web directory
echo "Creating web directory..."
mkdir -p $WEBROOT
chown -R www-data:www-data $WEBROOT

# 2. Create Nginx config
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/statt-tipex << 'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name statt-tipex.de www.statt-tipex.de;

    root /var/www/statt-tipex;
    index index.html;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # SPA: serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
NGINX

# 3. Enable site
ln -sf /etc/nginx/sites-available/statt-tipex /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "Nginx configured."

# 4. SSL with Let's Encrypt
echo "Setting up SSL..."
if ! command -v certbot &> /dev/null; then
    apt-get update && apt-get install -y certbot python3-certbot-nginx
fi

certbot --nginx -d statt-tipex.de -d www.statt-tipex.de --non-interactive --agree-tos --email admin@statt-tipex.de --redirect

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Copy index.html to $WEBROOT/"
echo "   scp index.html <user>@<server>:$WEBROOT/"
echo ""
echo "2. Visit https://statt-tipex.de"
echo ""
