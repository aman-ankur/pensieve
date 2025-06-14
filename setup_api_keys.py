#!/usr/bin/env python3
"""
Secure API Key Setup for Pensieve Production
Handles secure configuration of Claude API key with environment variables.
"""

import os
import sys
import yaml
import getpass
from pathlib import Path

def setup_production_config():
    """Set up production configuration with secure API key management."""
    
    print("🔐 Pensieve Production Setup")
    print("=" * 50)
    
    # Check if production config exists
    config_path = Path("config/production.yaml")
    if not config_path.exists():
        print("❌ Error: config/production.yaml not found")
        print("   Run this from the project root directory")
        return False
    
    # Get API key securely
    print("\n📋 Claude API Key Setup")
    print("Choose your preferred method:")
    print("1. Set environment variable (recommended)")
    print("2. Store in secure config file")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        setup_environment_variable()
    elif choice == "2":
        setup_config_file()
    else:
        print("❌ Invalid choice. Exiting.")
        return False
    
    # Test configuration
    test_config()
    
    print("\n✅ Production setup complete!")
    print("🚀 Ready to run hybrid Pensieve system")
    
    return True

def setup_environment_variable():
    """Set up environment variable for API key."""
    
    print("\n🔑 Setting up environment variable...")
    
    # Get API key
    api_key = getpass.getpass("Enter your Anthropic API key (hidden): ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    if not api_key.startswith("sk-ant-"):
        print("⚠️  Warning: API key doesn't look like an Anthropic key")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Create .env file
    env_path = Path(".env")
    with open(env_path, 'w') as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")
    
    print(f"✅ Created .env file with API key")
    print("💡 To use: export ANTHROPIC_API_KEY from .env or run with python-dotenv")
    
    # Show usage instructions
    print("\n📖 Usage Instructions:")
    print("   Option 1: source .env && python main.py")
    print("   Option 2: python-dotenv run python main.py")
    print("   Option 3: export $(cat .env) && python main.py")

def setup_config_file():
    """Set up config file with API key (less secure)."""
    
    print("\n⚠️  Warning: This stores API key in plain text config file")
    confirm = input("Are you sure? (y/N): ").strip().lower()
    if confirm != 'y':
        return False
    
    # Get API key
    api_key = getpass.getpass("Enter your Anthropic API key (hidden): ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Read production config
    config_path = Path("config/production.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update API key
    config['ai_providers']['claude']['api_key'] = api_key
    
    # Write updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print("✅ Updated config/production.yaml with API key")
    print("⚠️  Remember: This file contains your API key in plain text")

def test_config():
    """Test the configuration setup."""
    
    print("\n🧪 Testing Configuration...")
    
    try:
        # Test environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print(f"✅ Environment variable: Found (***{api_key[-8:]})")
        else:
            print("⚪ Environment variable: Not set")
        
        # Test config file
        config_path = Path("config/production.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            claude_config = config.get('ai_providers', {}).get('claude', {})
            config_api_key = claude_config.get('api_key', '')
            
            if config_api_key and not config_api_key.startswith('${'):
                print(f"✅ Config file: API key found (***{config_api_key[-8:]})")
            else:
                print("⚪ Config file: Using environment variable placeholder")
        
        print("✅ Configuration test complete")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def main():
    """Main setup function."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_config()
        return
    
    setup_production_config()

if __name__ == "__main__":
    main() 