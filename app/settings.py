# ============================================
# CLEANUP AND STORAGE MANAGEMENT SETTINGS
# ============================================

# ZIP Files Retention
# Retention period for generated certificate zip files (in hours)
# Default: 48 hours - users can re-download within this window
ZIP_RETENTION_HOURS = 48

# Temporary Files
# If True: automatically deletes all temp Excel and processing files after each generation
# If False: keeps temp files (NOT recommended - wastes space)
AUTO_CLEANUP_TEMP = True

# Template Management
# Number of old templates to keep on server
# Default: 2 - keeps current + 1 backup, deletes older versions
KEEP_OLD_TEMPLATES = 2

# PDF Storage
# If True: deletes individual PDFs after zipping (saves ~80% space)
# If False: keeps both PDFs and zip files
DELETE_PDFS_AFTER_ZIP = True

# System Management
# Enable automatic cleanup on each generation
AUTO_CLEANUP_ENABLED = True

# Maximum zip files to keep on server at any time
MAX_ZIP_FILES = 100

# ============================================
# CLEANUP ENDPOINTS
# ============================================
# Manual cleanup can be triggered at: GET /cleanup
# This will immediately delete:
#   - Old zip files (older than ZIP_RETENTION_HOURS)
#   - All temp Excel files
#   - Old template backups
#   - Empty job directories
#
# Recommended: Set up a cron job to call /cleanup every 6-12 hours
# Example cron: 0 */6 * * * curl http://localhost:8000/cleanup
# ============================================

# ============================================
# STORAGE OPTIMIZATION
# ============================================
# Current setup optimizes for:
# ✓ Minimal disk space usage
# ✓ Automatic cleanup
# ✓ User experience (zip available for 48 hours)
# ✓ No manual intervention required
#
# Expected storage savings:
# - ~80% reduction from deleting PDFs after zip
# - Additional savings from temp file cleanup
# - Old templates removed automatically
# ============================================

