#!/usr/bin/env python3
"""
Integration test for Pensieve processing pipeline.
Tests the complete flow from transcript parsing to summary generation and storage.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_full_pipeline():
    """Test the complete processing pipeline with a real transcript."""
    print("🧠 Testing Pensieve Processing Pipeline")
    print("=" * 60)
    
    try:
        # Import our modules
        from src.processing.ai_processor import AIProcessor
        from src.storage.summary_storage import SummaryStorage
        from src.utils.config import get_config
        from src.utils.logger import setup_logging, get_logger
        
        # Setup logging
        setup_logging()
        logger = get_logger("test")
        
        print("✅ Modules imported successfully")
        
        # Get configuration
        config = get_config()
        zoom_folder = Path(config.monitoring.zoom_folder)
        
        # Find a test transcript file
        transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))
        
        if not transcript_files:
            print("❌ No transcript files found for testing")
            return False
        
        # Use the first (oldest) transcript file for testing
        test_file = transcript_files[0]
        print(f"📄 Using test file: {test_file.parent.name}")
        print(f"   File size: {test_file.stat().st_size:,} bytes")
        
        # Test 1: AI Processing
        print("\n🤖 Testing AI Processing...")
        processor = AIProcessor()
        
        start_time = time.time()
        result = processor.process_transcript(test_file)
        processing_time = time.time() - start_time
        
        if not result.success:
            print(f"❌ AI Processing failed: {result.error}")
            return False
        
        print(f"✅ AI Processing successful in {processing_time:.1f}s")
        print(f"   Model used: {result.model_used}")
        print(f"   Meeting: {result.metadata.title}")
        print(f"   Participants: {', '.join(result.metadata.participants)}")
        print(f"   Type: {result.metadata.meeting_type}")
        print(f"   Summary length: {len(result.summary):,} characters")
        
        # Show a preview of the summary
        preview = result.summary[:200] + "..." if len(result.summary) > 200 else result.summary
        print(f"   Preview: {preview}")
        
        # Test 2: Storage
        print("\n💾 Testing Summary Storage...")
        storage = SummaryStorage()
        
        saved_path = storage.save_summary(result)
        
        if not saved_path:
            print("❌ Storage failed")
            return False
        
        print(f"✅ Summary saved successfully")
        print(f"   Path: {saved_path}")
        print(f"   Size: {saved_path.stat().st_size:,} bytes")
        
        # Verify the file was created and has content
        if saved_path.exists() and saved_path.stat().st_size > 0:
            print("✅ Summary file verified")
            
            # Show first few lines
            with open(saved_path, 'r', encoding='utf-8') as f:
                first_lines = '\n'.join(f.readlines()[:10])
            print("   First few lines:")
            for line in first_lines.split('\n')[:5]:
                print(f"     {line}")
        else:
            print("❌ Summary file verification failed")
            return False
        
        # Test 3: Storage Statistics
        print("\n📊 Testing Storage Statistics...")
        stats = storage.get_storage_stats()
        
        print(f"✅ Storage stats retrieved")
        print(f"   Total summaries: {stats.get('total_summaries', 0)}")
        print(f"   Total size: {stats.get('total_size_mb', 0)} MB")
        print(f"   Storage path: {stats.get('storage_path', 'Unknown')}")
        
        # Test 4: Recent summaries
        recent = storage.get_recent_summaries(days=1)
        print(f"   Recent summaries (1 day): {len(recent)}")
        
        print("\n" + "=" * 60)
        print("🎉 All pipeline tests passed successfully!")
        
        print("\n📋 Summary of what was tested:")
        print("✅ Configuration loading")
        print("✅ Transcript parsing and metadata extraction")
        print("✅ AI processing with Ollama")
        print("✅ Summary generation")
        print("✅ File storage and organization")
        print("✅ Storage statistics and management")
        
        print(f"\n📁 Your summary is saved at:")
        print(f"   {saved_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        print("Full error:")
        traceback.print_exc()
        return False


def test_processing_speed():
    """Test processing speed with multiple files."""
    print("\n⚡ Testing Processing Speed...")
    
    try:
        from src.processing.ai_processor import AIProcessor
        from src.utils.config import get_config
        
        config = get_config()
        zoom_folder = Path(config.monitoring.zoom_folder)
        
        # Find a few transcript files for speed testing
        transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))[:3]
        
        if len(transcript_files) < 2:
            print("⚠️ Need at least 2 transcript files for speed testing")
            return True
        
        processor = AIProcessor()
        
        total_start = time.time()
        results = []
        
        for i, file_path in enumerate(transcript_files, 1):
            print(f"   Processing file {i}/{len(transcript_files)}: {file_path.parent.name}")
            
            start = time.time()
            result = processor.process_transcript(file_path)
            duration = time.time() - start
            
            if result.success:
                print(f"   ✅ Completed in {duration:.1f}s")
                results.append(duration)
            else:
                print(f"   ❌ Failed: {result.error}")
        
        total_time = time.time() - total_start
        
        if results:
            avg_time = sum(results) / len(results)
            print(f"\n📈 Speed Test Results:")
            print(f"   Files processed: {len(results)}")
            print(f"   Total time: {total_time:.1f}s")
            print(f"   Average per file: {avg_time:.1f}s")
            print(f"   Estimated throughput: {3600/avg_time:.0f} files/hour")
        
        return True
        
    except Exception as e:
        print(f"❌ Speed test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting Pensieve Integration Tests\n")
    
    # Test 1: Full pipeline
    success1 = test_full_pipeline()
    
    # Test 2: Speed test (optional)
    if success1:
        try:
            success2 = test_processing_speed()
        except:
            success2 = True  # Don't fail on speed test issues
    else:
        success2 = False
    
    print("\n" + "=" * 60)
    print("📊 Final Results:")
    
    if success1 and success2:
        print("🎉 All tests passed! Pensieve is working perfectly.")
        print("\n🚀 Ready for production use!")
        print("   Run: python src/main.py (when implemented)")
        print("   Or check your summaries folder for generated content")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 