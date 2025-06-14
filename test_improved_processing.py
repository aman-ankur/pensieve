#!/usr/bin/env python3
"""
Test script to validate improved prompt templates.
"""

import sys
from pathlib import Path
from src.processing.ai_processor import AIProcessor
from src.utils.logger import get_logger

def main():
    logger = get_logger("test_improved")
    
    # Test file path
    test_file = Path("tests/test_transcripts/2025-02-14 16.59.24 Matteo _ Aman weekly syncup/meeting_saved_closed_caption.txt")
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return 1
    
    logger.info("🧪 Testing improved prompt templates...")
    logger.info(f"📁 Processing: {test_file.parent.name}")
    
    # Initialize processor
    processor = AIProcessor()
    
    # Process the transcript
    result = processor.process_transcript(test_file)
    
    if result.success:
        logger.info(f"✅ Processing successful in {result.processing_time:.1f}s")
        logger.info(f"📊 Chunks processed: {result.chunks_processed}")
        logger.info(f"🤖 Model used: {result.model_used}")
        
        # Save result
        output_file = Path("tests/context_aware_summary.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Context-Aware Summary Test\n")
            f.write(f"**Processing Time**: {result.processing_time:.1f}s\n")
            f.write(f"**Chunks**: {result.chunks_processed}\n")
            f.write(f"**Model**: {result.model_used}\n\n")
            f.write("---\n\n")
            f.write(result.summary)
        
        logger.info(f"💾 Summary saved to: {output_file}")
        
        # Show first few lines of summary
        lines = result.summary.split('\n')[:10]
        logger.info("📋 Summary preview:")
        for line in lines:
            if line.strip():
                logger.info(f"   {line}")
        
        return 0
    else:
        logger.error(f"❌ Processing failed: {result.error}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 