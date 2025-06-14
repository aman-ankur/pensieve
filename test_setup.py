#!/usr/bin/env python3
"""
Quick test script to verify Pensieve setup is working correctly.
Tests configuration loading, logging, and Ollama connectivity.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration loading...")
    
    try:
        from src.utils.config import get_config
        config = get_config()
        
        print(f"✅ Configuration loaded successfully!")
        print(f"   Zoom folder: {config.monitoring.zoom_folder}")
        print(f"   AI model: {config.processing.model_name}")
        print(f"   Summaries folder: {config.output.summaries_folder}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def test_logging():
    """Test logging setup."""
    print("\n📝 Testing logging setup...")
    
    try:
        from src.utils.logger import setup_logging, get_logger, log_system_info
        
        # Setup logging
        logger = setup_logging()
        
        # Test basic logging
        main_logger = get_logger()
        main_logger.info("Test log message from main logger")
        
        # Test child logger
        test_logger = get_logger("test")
        test_logger.info("Test log message from child logger")
        
        # Test system info logging
        log_system_info()
        
        print("✅ Logging setup successful!")
        return True
        
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        return False


def test_ollama_connectivity():
    """Test Ollama API connectivity."""
    print("\n🤖 Testing Ollama connectivity...")
    
    try:
        import requests
        from src.utils.config import get_config
        
        config = get_config()
        ollama_url = config.processing.ollama_url
        
        # Test if Ollama is running
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            model_names = [model['name'] for model in models.get('models', [])]
            
            print(f"✅ Ollama is running!")
            print(f"   Available models: {model_names}")
            
            # Check if our configured model is available
            target_model = config.processing.model_name
            if target_model in model_names:
                print(f"✅ Target model '{target_model}' is available!")
            else:
                print(f"⚠️  Target model '{target_model}' not found. Available: {model_names}")
            
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running? Try: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False


def test_zoom_folder_access():
    """Test access to Zoom folder."""
    print("\n📁 Testing Zoom folder access...")
    
    try:
        from src.utils.config import get_config
        
        config = get_config()
        zoom_folder = Path(config.monitoring.zoom_folder)
        
        if zoom_folder.exists():
            print(f"✅ Zoom folder exists: {zoom_folder}")
            
            # Count transcript files
            transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))
            print(f"   Found {len(transcript_files)} transcript files")
            
            if transcript_files:
                # Show a few examples
                for i, file_path in enumerate(transcript_files[:3]):
                    file_size = file_path.stat().st_size
                    print(f"   📄 {file_path.parent.name} ({file_size:,} bytes)")
                
                if len(transcript_files) > 3:
                    print(f"   ... and {len(transcript_files) - 3} more")
            
            return True
        else:
            print(f"❌ Zoom folder not found: {zoom_folder}")
            print("   Make sure Zoom is configured to save transcripts to ~/Documents/Zoom")
            return False
            
    except Exception as e:
        print(f"❌ Zoom folder test failed: {e}")
        return False


def main():
    """Run all setup tests."""
    print("🧠 Pensieve Setup Verification")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_logging,
        test_ollama_connectivity,
        test_zoom_folder_access
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    test_names = [
        "Configuration Loading",
        "Logging Setup", 
        "Ollama Connectivity",
        "Zoom Folder Access"
    ]
    
    all_passed = True
    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} | {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Pensieve is ready for development.")
        print("\nNext steps:")
        print("1. Run: python src/main.py (once implemented)")
        print("2. Check logs in: ./logs/pensieve.log") 
        print("3. Summaries will appear in: ./summaries/")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main() 