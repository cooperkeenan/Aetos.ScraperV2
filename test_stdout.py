#!/usr/bin/env python3
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Test 1: Direct print
logger.info("TEST 1: Direct print to stdout")
sys.stdout.write("TEST 2: sys.stdout.write\n")
sys.stdout.flush()

# Test 3: Logging
logger.info("TEST 3: Logger output")
sys.stdout.flush()

# Wait so container doesn't exit instantly
logger.info("Waiting 10 seconds before exit...")
time.sleep(10)
logger.info("Done!")
