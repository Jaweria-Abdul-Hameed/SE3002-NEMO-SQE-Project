#!/usr/bin/env python3
"""
Package repository submission zip with exact naming:
Project_24I-3025_24I-3135_24P-3099_A.zip
Strictly includes the .git directory to preserve per-member commit history.
Excludes transient caches (venv, node_modules, __pycache__, .pytest_cache).
"""

import os
import zipfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
ZIP_NAME = "Project_24I-3025_24I-3135_24P-3099_A.zip"
ZIP_PATH = WORKSPACE / ZIP_NAME

EXCLUDE_DIRS = {
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".cosmic-ray",
    ".mypy_cache",
    "test-results",
    "playwright-report",
    ".scannerwork",
}

EXCLUDE_FILES = {
    ZIP_NAME,
    ".coverage",
}

def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    for d in EXCLUDE_DIRS:
        if d in parts:
            return True
    if rel_path.name in EXCLUDE_FILES:
        return True
    if rel_path.suffix == ".pyc":
        return True
    return False

def package_zip():
    print(f"Creating submission zip: {ZIP_PATH}")
    total_files = 0
    git_files = 0

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(WORKSPACE):
            root_path = Path(root)
            rel_root = root_path.relative_to(WORKSPACE)

            # Skip excluded directories
            if any(part in EXCLUDE_DIRS for part in rel_root.parts):
                continue

            for file in files:
                file_path = root_path / file
                rel_file = file_path.relative_to(WORKSPACE)

                if should_exclude(rel_file):
                    continue

                zipf.write(file_path, arcname=str(rel_file))
                total_files += 1
                if ".git" in rel_file.parts:
                    git_files += 1

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"Zip created successfully!")
    print(f"Total files packaged: {total_files} (including {git_files} .git files)")
    print(f"Final archive size: {size_mb:.2f} MB")

if __name__ == "__main__":
    package_zip()
