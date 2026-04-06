#!/usr/bin/env bash
# Build script for Render Static Site

set -e

echo "Installing dependencies..."
npm install

echo "Building application..."
npm run build

echo "Build complete! Output in 'build' directory."

