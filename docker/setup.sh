#!/bin/bash
set -e

echo "🚀 Starting TrackFlow local development setup..."

# Wait for database
echo "⏳ Waiting for MariaDB to be ready..."
while ! mariadb -h mariadb -u frappe -pfrappe -e "SELECT 1;" > /dev/null 2>&1; do
    echo "Waiting for database..."
    sleep 5
done
echo "✅ Database is ready"

# Wait for Redis
echo "⏳ Waiting for Redis to be ready..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

cd /workspace/development/frappe-bench

# Check if site exists
SITE_NAME=${FRAPPE_SITE_NAME:-trackflow.localhost}

if [ ! -d "sites/$SITE_NAME" ]; then
    echo "🏗️ Creating new Frappe site: $SITE_NAME"
    
    # Install required apps first
    echo "📦 Getting Frappe CRM..."
    if [ ! -d "apps/crm" ]; then
        bench get-app crm --branch develop
    fi
    
    # Create site
    bench new-site $SITE_NAME \
        --mariadb-root-password admin \
        --admin-password admin \
        --db-name frappe_db \
        --db-host mariadb \
        --db-port 3306
        
    # Install apps
    echo "📦 Installing Frappe CRM..."
    bench --site $SITE_NAME install-app crm
    
    # Install TrackFlow
    echo "📦 Installing TrackFlow..."
    bench --site $SITE_NAME install-app trackflow
    
    echo "✅ Site created successfully!"
else
    echo "✅ Site $SITE_NAME already exists"
fi

# Set as current site
bench use $SITE_NAME

# Enable developer mode
bench --site $SITE_NAME set-config developer_mode 1
bench --site $SITE_NAME set-config disable_website_cache 1

# Configure database and redis
bench --site $SITE_NAME set-config db_host mariadb
bench --site $SITE_NAME set-config db_port 3306
bench --site $SITE_NAME set-config redis_cache "redis://redis:6379/0"
bench --site $SITE_NAME set-config redis_queue "redis://redis:6379/1"
bench --site $SITE_NAME set-config redis_socketio "redis://redis:6379/2"

# Clear cache and migrate
echo "🔄 Running migrations..."
bench --site $SITE_NAME migrate

echo "🎉 TrackFlow is ready!"
echo "📍 Access your site at: http://localhost:8000"
echo "👤 Admin credentials: Administrator / admin"
echo ""
echo "🚀 Starting development server..."

# Start the development server
bench start