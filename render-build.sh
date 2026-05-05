#!/usr/bin/env bash
# Exit on error
set -o errexit

# --- FRONTEND BUILD ---
echo "Building Frontend..."
cd frontend

# Dynamically replace localhost to allow relative paths in production
# This handles the hardcoded 'http://localhost:5000' without permanently modifying local source files
find src -type f -name "*.js" -exec sed -i 's|http://localhost:5000||g' {} +

npm install
npm run build
cd ..

# --- BACKEND BUILD ---
echo "Building Backend..."
pip install --upgrade pip
pip install -r requirements.txt
