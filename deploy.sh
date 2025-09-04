#!/bin/bash

# TrackFlow Deployment Script
# This script deploys the latest TrackFlow changes to your Frappe site

echo "🚀 Starting TrackFlow deployment..."

# Check if site name is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh [site-name]"
    echo "Example: ./deploy.sh site1.local"
    exit 1
fi

SITE_NAME=$1

echo "📦 Pulling latest changes from GitHub..."
git pull origin main

echo "🔧 Installing/updating app on site: $SITE_NAME"
bench --site $SITE_NAME install-app trackflow || bench --site $SITE_NAME migrate

echo "🎯 Clearing cache..."
bench --site $SITE_NAME clear-cache

echo "🔄 Restarting services..."
bench restart

echo "✅ TrackFlow deployment complete!"
echo ""
echo "📋 Next steps to test:"
echo "1. Log into your Frappe CRM instance"
echo "2. Check if 'TrackFlow' appears in the sidebar"
echo "3. Navigate to TrackFlow > Campaigns"
echo "4. Create a test campaign and tracked link"
echo "5. Test the bulk link generation at: TrackFlow > Campaigns > [Select Campaign] > Bulk Generate Links"
echo ""
echo "🔍 Troubleshooting:"
echo "- If TrackFlow doesn't appear in sidebar: bench --site $SITE_NAME reload-doctype-cache"
echo "- If module import errors persist: bench --site $SITE_NAME console (then import trackflow.api.links)"
echo "- Check error logs: bench --site $SITE_NAME console (then frappe.get_doc('Error Log', {'method': ['like', '%trackflow%']}))"
