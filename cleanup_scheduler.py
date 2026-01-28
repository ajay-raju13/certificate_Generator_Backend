#!/usr/bin/env python3
"""
Scheduled Cleanup Script
Run this periodically (e.g., via cron) to clean up old files

Usage:
    python cleanup_scheduler.py

For cron scheduling:
    0 */6 * * * /usr/bin/python3 /path/to/cleanup_scheduler.py
    (runs every 6 hours)
"""

import sys
from pathlib import Path
import requests
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
CLEANUP_INTERVAL_HOURS = 6  # Run cleanup every 6 hours


def run_cleanup():
    """Execute cleanup via API endpoint"""
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled cleanup...")
        
        # Get storage info before
        info_response = requests.get(f"{API_BASE_URL}/storage-info", timeout=30)
        if info_response.status_code == 200:
            storage_before = info_response.json()
            print(f"Storage before cleanup: {storage_before['storage']}")
        
        # Run cleanup
        cleanup_response = requests.post(f"{API_BASE_URL}/storage-cleanup", timeout=300)
        if cleanup_response.status_code == 200:
            result = cleanup_response.json()
            print(f"Cleanup completed successfully!")
            print(f"Stats: {result['cleanup_stats']}")
            print(f"Storage after: {result['storage_after']}")
            return True
        else:
            print(f"Cleanup failed with status {cleanup_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {API_BASE_URL}")
        print("Make sure the API server is running")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_cleanup()
    sys.exit(0 if success else 1)
