#!/bin/bash

# Simple run script for LlamaShared Chatbot

echo "🦙 Starting LlamaShared Chatbot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API credentials before running again."
    echo "   Required: LLAMASHARED_API_URL and LLAMASHARED_API_KEY"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Please run setup.sh first."
    echo "   ./setup.sh"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📋 Checking dependencies..."
pip list | grep streamlit > /dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing missing dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "🚀 Starting Streamlit application..."
echo "   Access the app at: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

streamlit run app.py
