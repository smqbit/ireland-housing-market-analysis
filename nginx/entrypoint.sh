#!/bin/sh
set -e

CERT=/etc/nginx/certs/cert.pem
KEY=/etc/nginx/certs/key.pem

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    echo "Generating self-signed SSL certificate..."
    mkdir -p /etc/nginx/certs

    EXTERNAL_IP=$(curl -sf --connect-timeout 2 \
        "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" \
        -H "Metadata-Flavor: Google" 2>/dev/null || hostname -i 2>/dev/null || echo "localhost")

    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "$KEY" -out "$CERT" \
        -subj "/CN=$EXTERNAL_IP" 2>/dev/null || \
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "$KEY" -out "$CERT" \
        -subj "/CN=localhost" 2>/dev/null

    echo "Certificate generated for: $EXTERNAL_IP"
else
    echo "Using existing certificate"
fi

exec nginx -g "daemon off;"