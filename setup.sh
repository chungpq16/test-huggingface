#!/bin/bash

# Setup script for LlamaShared Chatbot

echo "🦙 Setting up LlamaShared Chatbot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "✏️ Please edit .env file with your API credentials:"
    echo "   - LLAMASHARED_API_KEY=your_token_here"
    echo "   - LLAMASHARED_API_URL=your_api_url_here"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To run the application:"
echo "   1. Edit .env with your credentials"
echo "   2. source venv/bin/activate"
echo "   3. cd frontend"
echo "   4. streamlit run app.py"
