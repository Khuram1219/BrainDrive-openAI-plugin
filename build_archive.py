#!/usr/bin/env python3
"""
Plugin Archive Builder

This script creates a tar.gz archive of a plugin directory in the current PluginBuild folder.
Usage: python build_archive.py <plugin_name> <version>

Example: python build_archive.py NetworkEyes 1.0.3
Output: NetworkEyes-v1.0.3.tar.gz
"""

import os
import sys
import tarfile
import argparse
from pathlib import Path


def should_exclude_file(tarinfo):
    """
    Filter function to exclude certain files and directories from the archive
    
    Args:
        tarinfo: TarInfo object representing a file or directory
        
    Returns:
        None if the file should be excluded, tarinfo otherwise
    """
    # Get the path components
    path_parts = Path(tarinfo.name).parts
    
    # Exclude node_modules directories (at any level)
    if 'node_modules' in path_parts:
        return None

    # Exclude .git directories (at any level)
    if '.git' in path_parts:
        return None
    
    # Exclude package-lock.json files
    if tarinfo.name.endswith('package-lock.json'):
        return None
    
    return tarinfo


def create_plugin_archive(plugin_name: str, version: str):
    """
    Create a tar.gz archive of a plugin directory in the current directory
    Excludes node_modules directories and package-lock.json files
    
    Args:
        plugin_name: Name of the plugin directory to archive
        version: Version number for the archive
    """
    # Ensure version starts with 'v' if not already
    if not version.startswith('v'):
        version = f'v{version}'
    
    # Define paths (current directory)
    current_dir = Path('.')
    # plugin_path = current_dir / plugin_name
    plugin_path = current_dir
    archive_name = f"{plugin_name}-{version}.tar.gz"
    archive_path = current_dir / archive_name
    
    # Validate plugin directory exists
    if not plugin_path.exists():
        print(f"❌ Error: Plugin directory '{plugin_name}' does not exist")
        print(f"Available directories:")
        for item in current_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                print(f"  - {item.name}")
        return False
    
    if not plugin_path.is_dir():
        print(f"❌ Error: '{plugin_name}' is not a directory")
        return False
    
    # Create the archive
    try:
        print(f"📦 Creating archive: {archive_name}")
        print(f"📁 Source directory: {plugin_name}")
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add the plugin directory to the archive with exclusion filter
            # Use arcname to control the directory name in the archive
            tar.add(plugin_path, arcname=plugin_name, filter=should_exclude_file)
        
        # Verify the archive was created
        if archive_path.exists():
            file_size = archive_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            print(f"✅ Archive created successfully!")
            print(f"📄 File: {archive_name}")
            print(f"📏 Size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
            
            # List contents of the archive for verification
            print(f"\n📋 Archive contents:")
            with tarfile.open(archive_path, 'r:gz') as tar:
                members = tar.getnames()
                for member in sorted(members)[:10]:  # Show first 10 files
                    print(f"  {member}")
                if len(members) > 10:
                    print(f"  ... and {len(members) - 10} more files")
                print(f"  Total files: {len(members)}")
            
            return True
        else:
            print(f"❌ Error: Archive was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating archive: {e}")
        return False


def list_existing_archives():
    """List existing tar.gz archives in the current directory"""
    current_dir = Path('.')
    
    archives = list(current_dir.glob("*.tar.gz"))
    if archives:
        print(f"📚 Existing archives:")
        for archive in sorted(archives):
            file_size = archive.stat().st_size / (1024 * 1024)
            print(f"  {archive.name} ({file_size:.2f} MB)")
    else:
        print(f"📚 No existing archives found")


def list_plugin_directories():
    """List available plugin directories in the current directory"""
    current_dir = Path('.')
    print(f"📁 Available plugin directories:")
    
    directories = []
    for item in current_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.endswith('.tar.gz'):
            directories.append(item.name)
    
    if directories:
        for directory in sorted(directories):
            print(f"  {directory}")
    else:
        print(f"  No plugin directories found")


def main():
    parser = argparse.ArgumentParser(
        description="Create a tar.gz archive of a plugin directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_archive.py NetworkEyes 1.0.3
  python build_archive.py MyPlugin v2.1.0
  python build_archive.py --list
        """
    )
    
    parser.add_argument(
        'plugin_name', 
        nargs='?',
        help='Name of the plugin directory to archive'
    )
    parser.add_argument(
        'version', 
        nargs='?',
        help='Version number for the archive (e.g., 1.0.3 or v1.0.3)'
    )
    parser.add_argument(
        '--list', 
        action='store_true',
        help='List existing archives and available plugin directories'
    )
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list:
        list_existing_archives()
        print()
        list_plugin_directories()
        return
    
    # Validate required arguments
    if not args.plugin_name or not args.version:
        parser.print_help()
        print(f"\n❌ Error: Both plugin_name and version are required")
        return
    
    # Create the archive
    success = create_plugin_archive(args.plugin_name, args.version)
    
    if success:
        print()
        list_existing_archives()
        print(f"\n🎉 Plugin archive created successfully!")
    else:
        print(f"\n💥 Failed to create plugin archive")
        sys.exit(1)


if __name__ == "__main__":
    main()