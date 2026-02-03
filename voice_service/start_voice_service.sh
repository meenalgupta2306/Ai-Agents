#!/bin/bash

# Voice Service Startup Script

echo "Starting Voice Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the Flask service
echo "Starting Flask server on port 5002..."
echo "Note: First startup will download XTTS model (~1.8GB) - this may take a few minutes"
python voice_service.py
