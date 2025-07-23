#!/bin/bash

echo "🧪 Testing Docker image locally..."

# Build the image
echo "📦 Building Docker image..."
docker build -t stripe-test .

# Stop any existing container
echo "🛑 Stopping existing containers..."
docker stop stripe-test-container 2>/dev/null || true
docker rm stripe-test-container 2>/dev/null || true

# Run the container
echo "🚀 Starting container..."
docker run -d --name stripe-test-container -p 8000:8000 -e PORT=8000 -e ENVIRONMENT=dev stripe-test

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 15

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Test root endpoint (NiceGUI application)
echo "🏠 Testing NiceGUI application..."
curl -f http://localhost:8000/ || echo "❌ NiceGUI application failed to respond"

# Show logs
echo "📋 Container logs:"
docker logs stripe-test-container

# Open browser
echo "🌐 Opening browser..."
open http://localhost:8000

echo "✅ Local testing complete!"
echo "💡 To stop: docker stop stripe-test-container"
echo "💡 To view logs: docker logs -f stripe-test-container"