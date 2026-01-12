#!/bin/bash
set -e

# Run script and write to BOTH stdout and file
python -u test_navigation.py 2>&1 | tee /app/logs/output.log

echo "=== Log file created at /app/logs/output.log ===" | tee -a /app/logs/output.log