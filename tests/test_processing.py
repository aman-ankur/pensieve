#!/usr/bin/env python3
"""
Test the complete pipeline processing functionality.
"""

import sys
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processing.ai_processor import AIProcessor
from storage.summary_storage import SummaryStorage
from utils.config import get_config
from utils.logger import get_logger, setup_logging


def main():
    """Test the complete processing pipeline with the specific file."""
    # Setup
    setup_logging()
    logger = get_logger("test_processing")
    config = get_config()
    
    print("🧪 Testing Improved Pensieve Processing Pipeline")
    print("=" * 60)
    
    # Initialize components
    processor = AIProcessor()
    storage = SummaryStorage()
    
    # Find the specific transcript file we want to test
    zoom_folder = Path(config.monitoring.zoom_folder).expanduser()
    target_file_name = "2025-02-14 16.59.24 Matteo _ Aman weekly syncup"
    
    # Look for the specific file
    target_file = None
    transcript_files = list(zoom_folder.rglob("meeting_saved_closed_caption.txt"))
    
    for transcript_file in transcript_files:
        if target_file_name in transcript_file.parent.name:
            target_file = transcript_file
            break
    
    if not target_file:
        print(f"❌ Target file '{target_file_name}' not found in Zoom folder")
        print("Available files:")
        for f in transcript_files[:5]:
            print(f"   - {f.parent.name}")
        return
    
    print(f"🎯 Testing with specific file: {target_file.parent.name}")
    print(f"📄 File size: {target_file.stat().st_size:,} bytes")
    
    print(f"\n🚀 Processing with improved prompts and fast chunking...")
    start_time = time.time()
    
    # Process the specific transcript
    result = processor.process_transcript(target_file)
    
    total_time = time.time() - start_time
    
    if result.success:
        print(f"\n✅ AI Processing completed in {result.processing_time:.1f}s")
        print(f"   Model used: {result.model_used}")
        print(f"   Meeting: {result.metadata.title}")
        print(f"   Participants: {', '.join(result.metadata.participants) if result.metadata.participants else 'None detected'}")
        print(f"   Type: {result.metadata.meeting_type}")
        print(f"   Chunks processed: {result.chunks_processed}")
        print(f"   Summary length: {len(result.summary):,} characters")
        
        # Test storage
        print(f"\n💾 Saving improved summary...")
        save_result = storage.save_summary(result.summary, result.metadata)
        
        if save_result["success"]:
            print("✅ Summary saved successfully")
            print(f"   Path: {save_result['relative_path']}")
            print(f"   Size: {save_result['file_size']:,} bytes")
            
            # Show preview of the improved summary
            full_path = storage.get_full_path(save_result["relative_path"])
            if full_path.exists():
                print(f"\n📖 Preview of improved summary:")
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Show first few lines after metadata
                lines = content.split('\n')
                preview_started = False
                preview_lines = []
                
                for line in lines:
                    if preview_started:
                        preview_lines.append(line)
                        if len(preview_lines) >= 15:  # Show first 15 lines of actual content
                            break
                    elif line.startswith('## 🎯 Meeting Purpose'):
                        preview_started = True
                        preview_lines.append(line)
                
                for line in preview_lines:
                    print(f"   {line}")
                
                if len(preview_lines) >= 15:
                    print("   ...")
                
                print(f"\n📁 Full summary saved at:")
                print(f"   {save_result['relative_path']}")
                
        else:
            print(f"❌ Failed to save summary: {save_result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Processing failed: {result.error}")
    
    print(f"\n⏱️ Performance Summary:")
    print(f"   Total processing time: {total_time:.1f}s")
    print(f"   Previous time: ~117.6s")
    print(f"   Improvement: {((117.6 - total_time) / 117.6 * 100):.1f}% faster" if total_time < 117.6 else f"   {((total_time - 117.6) / 117.6 * 100):.1f}% slower")
    
    print(f"\n🎉 Test completed! Check the summary file for quality improvements.")


if __name__ == "__main__":
    main() 