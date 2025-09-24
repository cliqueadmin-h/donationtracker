#!/usr/bin/env python3
"""
Cleanup script for Donation Opportunities Finder

Removes generated result files, cache directories, and temporary files.
"""

import os
import shutil
import glob

def cleanup_files():
    """Remove generated files and caches"""
    
    print("🧹 Cleaning up generated files...")
    
    # Remove generated result files
    result_patterns = [
        'donation_opportunities_*.json',
        'donation_opportunities_*.csv'
    ]
    
    for pattern in result_patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"   Removed: {file}")
            except OSError as e:
                print(f"   Error removing {file}: {e}")
    
    # Clean up results directory
    if os.path.exists('results'):
        try:
            for file in os.listdir('results'):
                file_path = os.path.join('results', file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"   Removed: {file_path}")
        except OSError as e:
            print(f"   Error cleaning results directory: {e}")
    
    # Remove Python cache directories
    cache_dirs = ['__pycache__', '.pytest_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   Removed: {cache_dir}/")
            except OSError as e:
                print(f"   Error removing {cache_dir}: {e}")
    
    # Remove temporary files
    temp_patterns = ['*.tmp', '*.temp', '*.pyc']
    for pattern in temp_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            try:
                os.remove(file)
                print(f"   Removed: {file}")
            except OSError as e:
                print(f"   Error removing {file}: {e}")
    
    print("✅ Cleanup completed!")
    
    # Show what's preserved
    print("\n📄 Preserved important files:")
    preserved = [
        'config.json',
        'credentials.json',  
        'token.json',
        'requirements.txt',
        '.env',
        '.gitignore'
    ]
    
    for file in preserved:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (not found)")


if __name__ == '__main__':
    cleanup_files()