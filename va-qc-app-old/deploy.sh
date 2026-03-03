#!/bin/bash
# VA QC App - Deploy Script for VPS

set -e

echo "=========================================="
echo "VA QC App - Deployment"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Warning: Not running as root. May need sudo for Docker."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Installing..."
    curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

cd "$(dirname "$0")"

echo ""
echo "Building VA QC App..."
docker-compose build --no-cache

echo ""
echo "Starting VA QC App..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "App URL: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8000"
echo ""
echo "Default credentials:"
echo "  Admin:   rob / vulcan123"
echo "  Manager: gideon / vulcan123"
echo "  Artisan: lerato / vulcan123"
echo "  Client:  demo / vulcan123"
echo ""
echo "To check logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""