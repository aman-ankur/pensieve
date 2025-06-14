#!/usr/bin/env python3
"""
Pensieve - AI-Powered Meeting Intelligence
Main entry point for the hybrid system with Universal Intelligence.

Usage:
    python pensieve_main.py                    # Process latest transcript
    python pensieve_main.py --watch            # Monitor mode
    python pensieve_main.py --file <path>      # Process specific file
    python pensieve_main.py --setup            # Setup API keys
    python pensieve_main.py --test             # Run tests
    python pensieve_main.py --stats            # Show statistics
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.processing.pensieve_hybrid_processor import create_pensieve_processor
from src.monitor.file_watcher import ZoomMonitor
from src.utils.logger import get_logger, setup_logging
from src.utils.config import get_config


def setup_api_keys():
    """Run the API key setup process."""
    try:
        from setup_api_keys import setup_production_config
        return setup_production_config()
    except ImportError:
        print("❌ setup_api_keys.py not found")
        return False


def run_tests():
    """Run the integration tests."""
    try:
        from test_hybrid_integration import run_integration_tests
        run_integration_tests()
        return True
    except ImportError:
        print("❌ test_hybrid_integration.py not found")
        return False


def process_single_file(file_path: Path) -> bool:
    """Process a single transcript file."""
    logger = get_logger("pensieve_main")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"🧠 Processing: {file_path.name}")
    print("-" * 60)
    
    try:
        # Create processor
        processor = create_pensieve_processor()
        
        # Process the file
        start_time = time.time()
        result = processor.process_transcript(file_path)
        processing_time = time.time() - start_time
        
        if result.success:
            print("✅ Processing completed successfully!")
            print(f"⏱️  Processing time: {processing_time:.1f}s")
            print(f"🎯 Meeting type: {result.meeting_analysis.meeting_type.value} "
                  f"(confidence: {result.meeting_analysis.confidence:.2f})")
            print(f"🤖 AI provider: {result.ai_provider_used}")
            print(f"📊 Quality score: {result.quality_metrics.overall_score:.2f}")
            print(f"🚀 Intelligence boost: +{result.intelligence_boost:.1f}%")
            
            if result.recommendations:
                print("\n💡 Recommendations:")
                for rec in result.recommendations:
                    print(f"   • {rec}")
            
            # Save summary
            summary_path = create_summary_file(result, file_path)
            print(f"📝 Summary saved: {summary_path}")
            
            return True
        else:
            print(f"❌ Processing failed: {result.error}")
            return False
            
    except Exception as e:
        logger.error(f"Processing error: {e}")
        print(f"❌ Error: {e}")
        return False


def create_summary_file(result, original_file: Path) -> Path:
    """Create a summary file from processing result."""
    config = get_config()
    summaries_folder = Path(config.output.summaries_folder)
    summaries_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    meeting_date = result.metadata.date.split()[0] if result.metadata.date else "unknown"
    meeting_title = result.metadata.title.replace(" ", "_").lower()
    meeting_type = result.meeting_analysis.meeting_type.value
    
    filename = f"{meeting_date}_{meeting_type}_{meeting_title}_summary.md"
    summary_path = summaries_folder / filename
    
    # Create enhanced summary with metadata
    enhanced_summary = f"""# {result.metadata.title}

**Meeting Intelligence Report**
- **Date**: {result.metadata.date}
- **Type**: {result.meeting_analysis.meeting_type.value} (confidence: {result.meeting_analysis.confidence:.2f})
- **Duration**: {result.metadata.duration}
- **Participants**: {', '.join(result.metadata.participants)}
- **AI Provider**: {result.ai_provider_used}
- **Quality Score**: {result.quality_metrics.overall_score:.2f}
- **Intelligence Boost**: +{result.intelligence_boost:.1f}%

---

{result.summary}

---

**Processing Metadata**
- **Processing Time**: {result.processing_time:.1f}s
- **Model Used**: {result.model_used}
- **Original File**: {original_file}
- **Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

**Quality Metrics**
- **Technical Terms**: {result.quality_metrics.technical_terms_count}
- **Action Items**: {result.quality_metrics.action_items_count}
- **Business Context**: {result.quality_metrics.business_context_score:.2f}
- **Clarity Score**: {result.quality_metrics.clarity_score:.2f}

**Recommendations**
{chr(10).join(f'- {rec}' for rec in result.recommendations) if result.recommendations else '- None'}
"""
    
    # Write summary file
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_summary)
    
    return summary_path


def find_latest_transcript() -> Optional[Path]:
    """Find the most recent Zoom transcript."""
    zoom_folder = Path.home() / "Documents" / "Zoom"
    
    if not zoom_folder.exists():
        print("❌ Zoom folder not found: ~/Documents/Zoom")
        return None
    
    # Find all transcript files
    transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))
    
    if not transcript_files:
        print("❌ No transcript files found in Zoom folder")
        return None
    
    # Return the most recent
    latest = max(transcript_files, key=lambda p: p.stat().st_mtime)
    return latest


def watch_mode():
    """Run in continuous monitoring mode."""
    print("👁️  Starting Pensieve Watch Mode")
    print("Monitoring ~/Documents/Zoom for new meetings...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Create processor once
        processor = create_pensieve_processor()
        
        # Create file monitor
        monitor = ZoomMonitor()
        
        def process_new_file(file_path: Path):
            """Callback for new files."""
            print(f"\n🆕 New meeting detected: {file_path.parent.name}")
            
            # Process the file
            result = processor.process_transcript(file_path)
            
            if result.success:
                summary_path = create_summary_file(result, file_path)
                print(f"✅ Processed: {result.meeting_analysis.meeting_type.value} meeting")
                print(f"📝 Summary: {summary_path}")
                print(f"🚀 Quality: {result.quality_metrics.overall_score:.2f} "
                      f"(+{result.intelligence_boost:.1f}% boost)")
            else:
                print(f"❌ Failed: {result.error}")
            
            print("-" * 40)
        
        # Start monitoring
        monitor.start_monitoring(process_new_file)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping watch mode...")
    except Exception as e:
        print(f"❌ Watch mode error: {e}")


def show_statistics():
    """Show processing statistics."""
    try:
        processor = create_pensieve_processor()
        stats = processor.get_processing_stats()
        
        print("📊 Pensieve Processing Statistics")
        print("=" * 40)
        print(f"Total Processed: {stats['total_processed']}")
        print(f"Claude Used: {stats['claude_used']}")
        print(f"Ollama Used: {stats['ollama_used']}")
        print(f"Average Quality: {stats['avg_quality_score']:.2f}")
        print(f"Intelligence Improvements: {stats['intelligence_improvements']}")
        
        print("\n🤖 Provider Status:")
        for provider, status in stats.get('provider_status', {}).items():
            status_emoji = "✅" if status.get('available') else "❌"
            print(f"  {status_emoji} {provider}: {status.get('model', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pensieve - AI-Powered Meeting Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pensieve_main.py                           # Process latest transcript
  python pensieve_main.py --watch                   # Monitor for new meetings
  python pensieve_main.py --file meeting.txt       # Process specific file
  python pensieve_main.py --setup                   # Setup Claude API key
  python pensieve_main.py --test                    # Run integration tests
  python pensieve_main.py --stats                   # Show statistics
        """
    )
    
    parser.add_argument('--file', '-f', type=Path, help='Specific transcript file to process')
    parser.add_argument('--watch', '-w', action='store_true', help='Monitor mode - watch for new meetings')
    parser.add_argument('--setup', '-s', action='store_true', help='Setup API keys')
    parser.add_argument('--test', '-t', action='store_true', help='Run integration tests')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    print("🧠 Pensieve - AI-Powered Meeting Intelligence")
    print("=" * 50)
    
    # Handle different modes
    if args.setup:
        print("🔐 Setting up API keys...")
        success = setup_api_keys()
        return 0 if success else 1
    
    elif args.test:
        print("🧪 Running integration tests...")
        success = run_tests()
        return 0 if success else 1
    
    elif args.stats:
        show_statistics()
        return 0
    
    elif args.watch:
        watch_mode()
        return 0
    
    elif args.file:
        print(f"📁 Processing specific file: {args.file}")
        success = process_single_file(args.file)
        return 0 if success else 1
    
    else:
        # Default: process latest transcript
        print("🔍 Finding latest Zoom transcript...")
        latest_file = find_latest_transcript()
        
        if latest_file:
            print(f"📁 Found: {latest_file.parent.name}")
            success = process_single_file(latest_file)
            return 0 if success else 1
        else:
            print("❌ No transcript files found")
            print("💡 Try: python pensieve_main.py --setup (to configure API keys)")
            print("💡 Try: python pensieve_main.py --watch (to monitor for new meetings)")
            return 1


if __name__ == "__main__":
    sys.exit(main()) 