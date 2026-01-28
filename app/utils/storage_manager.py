"""
Cleanup Utility Module
Handles all file cleanup and storage management tasks
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta


class StorageManager:
    """Manages file cleanup and disk space"""
    
    def __init__(self, output_dir, temp_dir, templates_dir, retention_hours=48):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.templates_dir = Path(templates_dir)
        self.retention_seconds = retention_hours * 3600
    
    def get_storage_info(self):
        """Get current storage usage information"""
        def get_dir_size(path):
            total = 0
            if path.exists():
                for entry in path.rglob('*'):
                    if entry.is_file():
                        total += entry.stat().st_size
            return total
        
        output_size = get_dir_size(self.output_dir)
        temp_size = get_dir_size(self.temp_dir)
        
        return {
            "output_dir_mb": round(output_size / (1024 * 1024), 2),
            "temp_dir_mb": round(temp_size / (1024 * 1024), 2),
            "total_mb": round((output_size + temp_size) / (1024 * 1024), 2)
        }
    
    def cleanup_old_zips(self, force=False):
        """Delete zip files older than retention period (or all if force=True)"""
        deleted_count = 0
        if not self.output_dir.exists():
            return deleted_count
        
        current_time = time.time()
        for item in self.output_dir.iterdir():
            if item.is_file() and item.suffix == '.zip':
                file_age = current_time - item.stat().st_mtime
                if force or file_age > self.retention_seconds:
                    try:
                        item.unlink()
                        deleted_count += 1
                        print(f"[{self._timestamp()}] Deleted zip: {item.name}")
                    except Exception as e:
                        print(f"Failed to delete {item.name}: {e}")
        return deleted_count
    
    def cleanup_job_dirs(self, force=False):
        """Delete job directories (all if force=True, otherwise specific logic if needed)"""
        deleted_count = 0
        if not self.output_dir.exists():
            return deleted_count
        
        current_time = time.time()
        for item in self.output_dir.iterdir():
            if item.is_dir():
                try:
                    # If force is True, delete everything. 
                    # If force is False, check age (retention) or simply delete if empty.
                    # Here we mimic old_zips logic: if older than retention > delete
                    created_age = current_time - item.stat().st_ctime
                    
                    should_delete = False
                    if force:
                        should_delete = True
                    elif created_age > self.retention_seconds:
                        should_delete = True
                    # Also delete if empty regardless of age (legacy logic)
                    elif not any(item.iterdir()):
                        should_delete = True

                    if should_delete:
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        print(f"[{self._timestamp()}] Deleted job folder: {item.name}")

                except Exception as e:
                    print(f"Failed to delete directory {item.name}: {e}")
        return deleted_count
    
    def cleanup_temp_files(self, force=False):
        """Delete temporary files (force=True deletes all)"""
        deleted_count = 0
        if not self.temp_dir.exists():
            return deleted_count
        
        current_time = time.time()
        for item in self.temp_dir.iterdir():
            try:
                # Check age for both files and directories
                file_age = current_time - item.stat().st_mtime
                if force or file_age > self.retention_seconds:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    deleted_count += 1
                    print(f"[{self._timestamp()}] Deleted temp: {item.name}")
            except Exception as e:
                print(f"Failed to delete {item.name}: {e}")
        return deleted_count
    
    def cleanup_old_templates(self, keep_count=2, force=False):
        """Keep only the latest N templates, or delete all if force=True"""
        deleted_count = 0
        if not self.templates_dir.exists():
            return deleted_count
        
        # If force, just delete everything
        if force:
            for f in self.templates_dir.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                        deleted_count += 1
                    except: pass
            return deleted_count
        
        # Normal logic
        templates = sorted(
            [f for f in self.templates_dir.iterdir() if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_template in templates[keep_count:]:
            try:
                old_template.unlink()
                deleted_count += 1
                print(f"[{self._timestamp()}] Deleted old template: {old_template.name}")
            except Exception as e:
                print(f"Failed to delete template {old_template.name}: {e}")
        return deleted_count
    
    def full_cleanup(self, force=False):
        """Run all cleanup tasks. Set force=True to delete everything immediately."""
        print(f"\n[{self._timestamp()}] === Starting Full Cleanup (Force={force}) ===")
        
        stats = {
            "old_zips": self.cleanup_old_zips(force=force),
            "job_dirs": self.cleanup_job_dirs(force=force),
            "temp_files": self.cleanup_temp_files(force=force),
            "old_templates": self.cleanup_old_templates(force=force)
        }
        
        storage_before = self.get_storage_info()
        print(f"[{self._timestamp()}] === Cleanup Complete ===")
        print(f"[{self._timestamp()}] Deleted: {sum(stats.values())} items")
        print(f"[{self._timestamp()}] Storage Info: {storage_before}")
        
        return stats
    
    @staticmethod
    def _timestamp():
        """Get formatted timestamp"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
