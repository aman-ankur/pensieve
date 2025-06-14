#!/usr/bin/env python3
"""Simple .env file loader for Pensieve"""

import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("📝 Creating .env file template...")
        with open(env_file, 'w') as f:
            f.write("""# Pensieve AI Configuration
# Add your actual API keys below

# Anthropic Claude API Key (optional - for hybrid cloud processing)
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=

# Future: Add other AI provider keys here
# OPENAI_API_KEY=
# GEMINI_API_KEY=
""")
        print(f"✅ Created {env_file}")
        print("📝 Please edit .env file and add your Anthropic API key")
        return False
    
    print("🔑 Loading environment variables from .env file...")
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if value and not value.startswith('your_') and not value == '':
                    os.environ[key] = value
                    print(f"✅ Loaded {key}")
    
    return True

if __name__ == "__main__":
    load_env() 