#!/bin/bash

# Check if the service is running
echo "Checking service status..."
./service.sh status || { echo "Service is not running. Exiting."; exit 1; }

# Define test URL
TEST_URL="https://en.wikipedia.org/wiki/ReMarkable"

# Run the test service script
echo "Running end-to-end test with URL: $TEST_URL"
./test_service.sh "$TEST_URL" > test_results.log 2>&1

# Check if the test service script succeeded
if [ $? -ne 0 ]; then
    echo "Test service script failed. Check test_results.log for details."
    exit 1
fi

# Verify generated files in the temp directory
echo "Checking generated files in the temp directory..."
python3 check_files.py > file_check_results.log 2>&1

# Check if the file check script succeeded
if [ $? -ne 0 ]; then
    echo "File check script failed. Check file_check_results.log for details."
    exit 1
fi

# Log test completion
echo "End-to-end test completed successfully. Results logged in test_results.log and file_check_results.log."
