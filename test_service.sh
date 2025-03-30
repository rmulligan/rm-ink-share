#!/bin/bash

# Test script for Pi Share Receiver
# Sends a test URL to the service

# Check if a URL was provided
if [ "$#" -ne 1 ]; then
    TEST_URL="https://en.wikipedia.org/wiki/ReMarkable"
    echo "No URL provided, using default: $TEST_URL"
else
    TEST_URL="$1"
    echo "Using provided URL: $TEST_URL"
fi

# Attempt to send the URL to the service
echo "Sending URL to Pi Share Receiver service..."
curl -X POST -H "Content-Type: application/json" -d "{\"url\":\"$TEST_URL\"}" http://localhost:9999/share

echo -e "\n\nCheck the service logs to see if the request was processed successfully."
echo "You can use './service.sh logs' to view the logs."