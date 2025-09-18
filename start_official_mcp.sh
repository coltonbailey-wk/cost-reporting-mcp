#!/bin/bash

echo "🚀 Starting AWS Cost Explorer Official MCP Server..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  AWS credentials not found. Please run 'aws configure' first."
    echo "   Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
    echo ""
fi

# Start the official MCP web application
echo "🌐 Starting Official MCP-enabled web server..."
echo "   Dashboard will be available at: http://localhost:8002"
echo "   MCP Server: Official AWS Cost Explorer MCP"
echo "   Press Ctrl+C to stop the server"
echo ""

python3 web_app.py
