#!/bin/bash

# Setup script for Pi Share Receiver dependencies
# Installs and configures required packages and tools

echo "Setting up dependencies for Pi Share Receiver..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
fi

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers (headless)..."
playwright install --with-deps chromium

# Create necessary directories
echo "Creating required directories..."
mkdir -p output
mkdir -p temp
mkdir -p temp/pdf_extract

echo "Checking installation of drawj2d and rmapi..."
# Check if drawj2d is installed
if ! command -v drawj2d &> /dev/null
then
    echo "WARNING: drawj2d command not found. Please install it manually."
    echo "You can find it at https://github.com/pbonnin-fork/drawj2d"
fi

# Check if rmapi is installed
if ! command -v rmapi &> /dev/null
then
    echo "WARNING: rmapi command not found. Please install it manually."
    echo "You can find it at https://github.com/juruen/rmapi"
fi

echo "Setup complete!"
echo "--------------------"
echo "Next steps:"
echo "1. Configure app/server.py with your paths"
echo "2. Run 'rmapi' once to authenticate with Remarkable Cloud"
echo "3. Start the server with 'python app/server.py' or './service.sh start'"