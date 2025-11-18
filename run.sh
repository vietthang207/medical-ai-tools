#!/bin/bash

# DICOM Viewer Web App Launch Script

echo "🏥 Starting DICOM Medical Image Viewer..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p uploads templates

# Check if templates/index.html exists
if [ ! -f "templates/index.html" ]; then
    echo "❌ Error: templates/index.html not found!"
    exit 1
fi

# Start the Flask app
echo ""
echo "✅ Starting Flask server..."
echo "🌐 Open your browser and navigate to: http://localhost:5000"
echo ""
python3 app.py

