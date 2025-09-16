#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Handler Utilities

Provides file and directory handling utilities for the similarity detection system.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class FileHandler:
    """
    Handles file operations for similarity detection system.
    """

    def __init__(self):
        """Initialize file handler."""
        pass

    def scan_markdown_files(self, directory: str) -> List[Path]:
        """
        Scan directory for Markdown files.

        Args:
            directory: Directory path to scan

        Returns:
            List of Markdown file paths
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            return []

        return list(directory_path.glob("*.md"))

    def safe_move_file(self, source: Path, target: Path, backup: bool = True) -> bool:
        """
        Safely move a file with optional backup.

        Args:
            source: Source file path
            target: Target file path
            backup: Whether to create backup if target exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            # Handle existing target file
            if target.exists():
                if backup:
                    backup_path = self._create_backup_path(target)
                    shutil.move(str(target), str(backup_path))
                    print(f"  📦 备份已存在文件: {target.name} → {backup_path.name}")
                else:
                    # Generate unique name
                    target = self._generate_unique_path(target)

            # Move the file
            shutil.move(str(source), str(target))
            return True

        except Exception as e:
            print(f"  ❌ 文件移动失败 {source.name} → {target.name}: {e}")
            return False

    def safe_copy_file(self, source: Path, target: Path) -> bool:
        """
        Safely copy a file.

        Args:
            source: Source file path
            target: Target file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            # Handle existing target file
            if target.exists():
                target = self._generate_unique_path(target)

            # Copy the file
            shutil.copy2(str(source), str(target))
            return True

        except Exception as e:
            print(f"  ❌ 文件复制失败 {source.name} → {target.name}: {e}")
            return False

    def _create_backup_path(self, file_path: Path) -> Path:
        """
        Create backup file path with timestamp.

        Args:
            file_path: Original file path

        Returns:
            Backup file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stem = file_path.stem
        suffix = file_path.suffix
        backup_name = f"{stem}_backup_{timestamp}{suffix}"
        return file_path.parent / backup_name

    def _generate_unique_path(self, file_path: Path) -> Path:
        """
        Generate unique file path to avoid conflicts.

        Args:
            file_path: Original file path

        Returns:
            Unique file path
        """
        if not file_path.exists():
            return file_path

        counter = 1
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        while True:
            new_name = f"{stem}_{counter:03d}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def create_directory_structure(self, base_dir: str, subdirs: List[str]) -> Dict[str, Path]:
        """
        Create directory structure.

        Args:
            base_dir: Base directory path
            subdirs: List of subdirectory names

        Returns:
            Dictionary mapping subdirectory names to paths
        """
        base_path = Path(base_dir)
        created_dirs = {}

        for subdir in subdirs:
            dir_path = base_path / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs[subdir] = dir_path

        return created_dirs

    def get_file_stats(self, file_path: Path) -> Dict[str, any]:
        """
        Get comprehensive file statistics.

        Args:
            file_path: File path

        Returns:
            Dictionary with file statistics
        """
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'exists': True
            }
        except Exception:
            return {
                'size': 0,
                'created': None,
                'modified': None,
                'accessed': None,
                'exists': False
            }

    def cleanup_empty_directories(self, directory: str) -> int:
        """
        Remove empty directories recursively.

        Args:
            directory: Root directory to clean

        Returns:
            Number of directories removed
        """
        removed_count = 0
        directory_path = Path(directory)

        if not directory_path.exists():
            return 0

        # Walk bottom-up to remove empty directories
        for root, dirs, files in os.walk(str(directory_path), topdown=False):
            root_path = Path(root)

            # Skip if directory contains files
            if files:
                continue

            # Skip if directory contains non-empty subdirectories
            if any((root_path / d).exists() and list((root_path / d).iterdir()) for d in dirs):
                continue

            # Remove empty directory
            try:
                root_path.rmdir()
                removed_count += 1
                print(f"  🗑️ 删除空目录: {root_path}")
            except Exception as e:
                print(f"  ⚠️ 无法删除目录 {root_path}: {e}")

        return removed_count

    def find_duplicate_filenames(self, directories: List[str]) -> Dict[str, List[str]]:
        """
        Find duplicate filenames across multiple directories.

        Args:
            directories: List of directory paths to check

        Returns:
            Dictionary mapping filenames to list of full paths
        """
        filename_map = {}

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for file_path in dir_path.glob("*.md"):
                filename = file_path.name
                if filename not in filename_map:
                    filename_map[filename] = []
                filename_map[filename].append(str(file_path))

        # Return only duplicates
        duplicates = {k: v for k, v in filename_map.items() if len(v) > 1}
        return duplicates

    def archive_files(self, files: List[Path], archive_dir: str,
                     date_suffix: bool = True) -> Tuple[int, int]:
        """
        Archive files to a specified directory.

        Args:
            files: List of files to archive
            archive_dir: Archive directory path
            date_suffix: Whether to add date suffix to archive directory

        Returns:
            Tuple of (successful_count, failed_count)
        """
        archive_path = Path(archive_dir)

        if date_suffix:
            date_str = datetime.now().strftime('%Y%m%d')
            archive_path = archive_path / date_str

        archive_path.mkdir(parents=True, exist_ok=True)

        successful_count = 0
        failed_count = 0

        for file_path in files:
            target_path = archive_path / file_path.name

            if self.safe_move_file(file_path, target_path):
                successful_count += 1
            else:
                failed_count += 1

        return successful_count, failed_count

    def get_directory_size(self, directory: str) -> Dict[str, int]:
        """
        Calculate directory size statistics.

        Args:
            directory: Directory path

        Returns:
            Dictionary with size statistics
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            return {'total_size': 0, 'file_count': 0, 'dir_count': 0}

        total_size = 0
        file_count = 0
        dir_count = 0

        for item in directory_path.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                    file_count += 1
                except Exception:
                    pass
            elif item.is_dir():
                dir_count += 1

        return {
            'total_size': total_size,
            'file_count': file_count,
            'dir_count': dir_count
        }