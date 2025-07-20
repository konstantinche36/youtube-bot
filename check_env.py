#!/usr/bin/env python3
"""Check environment variables"""

import os
from dotenv import load_dotenv

def main():
    """Check environment variables"""
    print("=== Environment Variables Check ===")
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
        load_dotenv()
    else:
        print("❌ .env file not found")
    
    # Check critical variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"TELEGRAM_BOT_TOKEN: {'✅ Set' if token else '❌ Not set'}")
    if token:
        print(f"  Length: {len(token)}")
        print(f"  Starts with: {token[:10]}...")
    
    # Check other variables
    variables = [
        "DATABASE_URL",
        "STORAGE_TYPE", 
        "LOG_LEVEL",
        "DEBUG"
    ]
    
    for var in variables:
        value = os.getenv(var)
        print(f"{var}: {'✅ Set' if value else '❌ Not set'}")
        if value:
            print(f"  Value: {value}")
    
    # Show all environment variables (be careful with sensitive data)
    print("\n=== All Environment Variables ===")
    for key, value in os.environ.items():
        if "TOKEN" in key or "SECRET" in key or "KEY" in key:
            print(f"{key}: {'*' * len(value) if value else 'None'}")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main() 