# Stop and remove container
docker stop stripe-test-container
docker rm stripe-test-container

# Remove image
docker rmi stripe-test

# Clean up all unused containers/images
docker system prune -f