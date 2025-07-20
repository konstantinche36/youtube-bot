#!/usr/bin/env python3
"""Create necessary directories"""

import os
from pathlib import Path

def main():
    """Create directories"""
    directories = [
        "./downloads",
        "./logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

if __name__ == "__main__":
    main() 