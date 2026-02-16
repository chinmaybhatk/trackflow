#!/bin/bash
set -e

echo "Building TrackFlow frontend..."

# Navigate to frontend directory
cd apps/trackflow/frontend

# Install dependencies
echo "Installing dependencies..."
yarn install --frozen-lockfile

# Build frontend
echo "Building Vue components..."
yarn build

echo "TrackFlow frontend build complete!"
