#!/bin/bash
set -e

# Mount will be at /app/logs if we attach Azure File Share
python -u test_navigation.py 2>&1 | tee /app/logs/output.log

echo "=== Log file created at /app/logs/output.log ==="