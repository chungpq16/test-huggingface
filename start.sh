#!/bin/bash

# Quick start script for HuggingFace Chatbot

echo "🤖 HuggingFace AI Chatbot - Quick Start"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 and pip3 are installed"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Ask user which version to run
echo ""
echo "Which version would you like to run?"
echo "1) Simple App (Recommended)"
echo "2) Advanced App (with LangChain)"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo "🚀 Starting Simple App..."
        streamlit run simple_app.py
        ;;
    2)
        echo "🚀 Starting Advanced App..."
        streamlit run app.py
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac
