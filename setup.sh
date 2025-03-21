#!/bin/bash

# Create a conda environment
echo "Creating conda environment..."
conda create -n agentic-newsletter python=3.10 -y
eval "$(conda shell.bash hook)"
conda activate agentic-newsletter

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "Setup complete!"
echo "To activate the environment, run: conda activate agentic-newsletter"
echo "Don't forget to download your Gmail API credentials.json file from the Google Cloud Console and change .env."
