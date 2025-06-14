#!/usr/bin/env python3
"""
Test configuration loading functionality.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import get_config


def test_config_loading():
    """Test that configuration loads properly."""
    print("🧪 Testing Configuration Loading")
    print("=" * 40)
    
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
        
        # Test monitoring config
        print(f"📁 Zoom folder: {config.monitoring.zoom_folder}")
        print(f"📝 File extensions: {getattr(config.monitoring, 'file_extensions', 'None')}")
        print(f"⏱️  Poll interval: {getattr(config.monitoring, 'poll_interval', 'None')}")
        
        # Test processing config
        print(f"🤖 Default model: {config.processing.model_name}")
        print(f"⚡ Chunk model: {getattr(config.processing, 'chunk_model', 'None')}")
        print(f"🧠 Synthesis model: {getattr(config.processing, 'synthesis_model', 'None')}")
        print(f"📊 Chunking config: {getattr(config.processing, 'chunking', 'None')}")
        
        # Test output config
        print(f"💾 Summaries folder: {config.output.summaries_folder}")
        print(f"🗓️  Organize by date: {getattr(config.output, 'organize_by_date', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


if __name__ == "__main__":
    success = test_config_loading()
    if success:
        print("\n🎉 Configuration test passed!")
    else:
        print("\n💥 Configuration test failed!")
        sys.exit(1) 