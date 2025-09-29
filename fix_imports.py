#!/usr/bin/env python3
"""
Fix absolute imports to relative imports in animation_converter package.

Usage:
    python fix_imports.py [--dry-run] [--backup]

Options:
    --dry-run    Show what would be changed without modifying files
    --backup     Create .bak backup files before modifying
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import List, Tuple


# List of internal modules that should use relative imports
INTERNAL_MODULES = [
    "anim_reorder",
    "build_utils",
    "cli_parser",
    "color_data_utils",
    "compress",
    "lzma_codec",
    "packer",
    "packer_config",
    "petscii",
    "rle_codec",
    "scroller",
    "utils",
]


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory, excluding gui and __pycache__"""
    python_files = []

    for file in directory.rglob("*.py"):
        # Skip __pycache__ and backup files
        if "__pycache__" in file.parts or file.suffix == ".bak":
            continue

        # Skip gui/app.py as it already has correct imports
        if "gui" in file.parts and file.name == "app.py":
            continue

        python_files.append(file)

    return sorted(python_files)


def fix_imports_in_content(content: str, filename: str) -> Tuple[str, List[str]]:
    """
    Fix imports in file content.
    Returns (fixed_content, list_of_changes)
    """
    lines = content.split("\n")
    changes = []
    fixed_lines = []

    for line_num, line in enumerate(lines, 1):
        original_line = line
        modified = False

        # Pattern 1: from module import ...
        for module in INTERNAL_MODULES:
            # Match: from module import ...
            pattern1 = rf"^(\s*)from {module} import (.+)$"
            match = re.match(pattern1, line)
            if match:
                indent, imports = match.groups()
                line = f"{indent}from .{module} import {imports}"
                modified = True
                changes.append(f"  Line {line_num}: from {module} → from .{module}")
                break

        # Pattern 2: import module
        if not modified:
            for module in INTERNAL_MODULES:
                pattern2 = rf"^(\s*)import {module}$"
                match = re.match(pattern2, line)
                if match:
                    indent = match.group(1)
                    line = f"{indent}from . import {module}"
                    modified = True
                    changes.append(
                        f"  Line {line_num}: import {module} → from . import {module}"
                    )
                    break

        fixed_lines.append(line)

    return "\n".join(fixed_lines), changes


def process_file(file_path: Path, dry_run: bool = False, backup: bool = False) -> bool:
    """
    Process a single file. Returns True if changes were made.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

    fixed_content, changes = fix_imports_in_content(original_content, file_path.name)

    if not changes:
        return False

    # Use absolute path to avoid relative_to issues
    try:
        display_path = file_path.relative_to(Path.cwd())
    except ValueError:
        display_path = file_path.absolute()

    print(f"\n📝 {display_path}")
    for change in changes:
        print(change)

    if dry_run:
        print("  [DRY RUN - no changes made]")
        return True

    # Create backup if requested
    if backup:
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)
        print(f"  💾 Backup created: {backup_path.name}")

    # Write fixed content
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)
        print("  ✅ File updated")
        return True
    except Exception as e:
        print(f"  ❌ Error writing file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix absolute imports to relative imports in animation_converter"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .bak backup files before modifying",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("src/animation_converter"),
        help="Directory to process (default: src/animation_converter)",
    )

    args = parser.parse_args()

    # Verify directory exists
    if not args.directory.exists():
        print(f"❌ Directory not found: {args.directory}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Please run from project root or specify --directory")
        return 1

    # Convert to absolute path to avoid issues
    args.directory = args.directory.resolve()

    print(f"🔍 Scanning {args.directory} for Python files...")
    python_files = find_python_files(args.directory)
    print(f"   Found {len(python_files)} Python files")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    if args.backup:
        print("💾 Backup mode enabled - .bak files will be created\n")

    files_changed = 0

    for file_path in python_files:
        if process_file(file_path, args.dry_run, args.backup):
            files_changed += 1

    print(f"\n{'='*60}")
    print(
        f"Summary: {files_changed} file(s) {'would be' if args.dry_run else 'were'} modified"
    )

    if args.dry_run and files_changed > 0:
        print("\nTo apply changes, run without --dry-run:")
        print(f"  python {Path(__file__).name}")

    return 0


if __name__ == "__main__":
    exit(main())
