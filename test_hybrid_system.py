#!/usr/bin/env python3
"""
Comprehensive test suite for the Pensieve Hybrid AI System.
Tests provider fallback, quality assessment, and overall functionality.
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_hybrid_system():
    """Test the complete hybrid AI system."""
    print("🧠 Testing Pensieve Hybrid AI System")
    print("=" * 60)
    
    try:
        # Import hybrid system components
        from src.processing.hybrid_ai_processor import HybridAIProcessor
        from src.processing.ai_providers import AIProviderManager
        from src.utils.config import get_config
        from src.utils.logger import setup_logging, get_logger
        
        # Setup logging
        setup_logging()
        logger = get_logger("test_hybrid")
        
        print("✅ Hybrid system modules imported successfully")
        
        # Initialize hybrid processor
        processor = HybridAIProcessor()
        print("✅ Hybrid AI Processor initialized")
        
        # Test 1: System Status Check
        print("\n🔍 Testing System Status...")
        status = processor.get_processing_status()
        
        print(f"   AI Providers: {len(status['ai_providers'])}")
        for provider_name, provider_status in status['ai_providers'].items():
            available = "✅" if provider_status['available'] else "❌"
            enabled = "✅" if provider_status['enabled'] else "❌"
            print(f"     {provider_name}: Available {available} | Enabled {enabled} | Priority: {provider_status['priority']}")
        
        print(f"   Prompt Templates: {len(status['prompt_templates'])}")
        print(f"   Processing Strategy: {status['processing_strategy']}")
        print(f"   Quality Assessment: {'✅' if status['features']['quality_assessment'] else '❌'}")
        
        # Test 2: Find Test Transcripts
        print("\n📄 Finding Test Transcripts...")
        config = get_config()
        zoom_folder = Path(config.monitoring.zoom_folder)
        
        transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))
        
        if not transcript_files:
            print("❌ No transcript files found for testing")
            print(f"   Check folder: {zoom_folder}")
            return False
        
        print(f"✅ Found {len(transcript_files)} transcript files")
        
        # Select test files by size for different test scenarios
        test_files = []
        for file_path in transcript_files[:5]:  # Test up to 5 files
            size_kb = file_path.stat().st_size / 1024
            test_files.append((file_path, size_kb))
        
        test_files.sort(key=lambda x: x[1])  # Sort by size
        
        # Test 3: Process with Hybrid System
        print("\n🚀 Testing Hybrid Processing...")
        results = []
        
        for i, (file_path, size_kb) in enumerate(test_files[:3], 1):
            print(f"\n   Test {i}/3: {file_path.parent.name} ({size_kb:.1f} KB)")
            
            start_time = time.time()
            result = processor.process_transcript(file_path)
            duration = time.time() - start_time
            
            if result.success:
                quality = result.quality_metrics
                print(f"   ✅ Success in {duration:.1f}s")
                print(f"      Provider: {result.ai_provider_used}")
                print(f"      Model: {result.model_used}")
                print(f"      Quality Score: {quality.overall_score:.2f}")
                print(f"      Confidence: {quality.confidence_level}")
                print(f"      Technical Terms: {quality.technical_terms_count}")
                print(f"      Action Items: {quality.action_items_count}")
                
                if quality.quality_issues:
                    print(f"      Quality Issues: {len(quality.quality_issues)}")
                    for issue in quality.quality_issues[:2]:
                        print(f"        - {issue}")
                
                results.append({
                    'file': file_path.parent.name,
                    'success': True,
                    'provider': result.ai_provider_used,
                    'quality_score': quality.overall_score,
                    'confidence': quality.confidence_level,
                    'duration': duration,
                    'size_kb': size_kb
                })
            else:
                print(f"   ❌ Failed: {result.error}")
                results.append({
                    'file': file_path.parent.name,
                    'success': False,
                    'error': result.error,
                    'duration': duration,
                    'size_kb': size_kb
                })
        
        # Test 4: Provider Comparison (if multiple providers available)
        print("\n⚖️ Testing Provider Comparison...")
        available_providers = [name for name, status in status['ai_providers'].items() 
                             if status['available'] and status['enabled']]
        
        if len(available_providers) > 1:
            test_file, _ = test_files[0]  # Use smallest file for comparison
            print(f"   Comparing providers using: {test_file.parent.name}")
            
            comparison_results = {}
            for provider_name in available_providers:
                print(f"   Testing with {provider_name}...")
                start_time = time.time()
                result = processor.regenerate_with_different_provider(test_file, provider_name)
                duration = time.time() - start_time
                
                if result.success:
                    quality = result.quality_metrics
                    comparison_results[provider_name] = {
                        'quality_score': quality.overall_score,
                        'confidence': quality.confidence_level,
                        'technical_terms': quality.technical_terms_count,
                        'action_items': quality.action_items_count,
                        'duration': duration
                    }
                    print(f"      ✅ Quality: {quality.overall_score:.2f}, Duration: {duration:.1f}s")
                else:
                    print(f"      ❌ Failed: {result.error}")
            
            if len(comparison_results) > 1:
                print("\n   📊 Provider Comparison Summary:")
                for provider, metrics in comparison_results.items():
                    print(f"      {provider}: Quality {metrics['quality_score']:.2f} | "
                          f"Speed {metrics['duration']:.1f}s | "
                          f"Confidence {metrics['confidence']}")
        else:
            print(f"   Only one provider available: {available_providers[0]}")
        
        # Test 5: Quality Assessment Analysis
        print("\n📈 Quality Assessment Analysis...")
        successful_results = [r for r in results if r['success']]
        
        if successful_results:
            avg_quality = sum(r['quality_score'] for r in successful_results) / len(successful_results)
            avg_duration = sum(r['duration'] for r in successful_results) / len(successful_results)
            
            providers_used = {}
            for r in successful_results:
                providers_used[r['provider']] = providers_used.get(r['provider'], 0) + 1
            
            print(f"   Average Quality Score: {avg_quality:.2f}")
            print(f"   Average Processing Time: {avg_duration:.1f}s")
            print(f"   Providers Used: {dict(providers_used)}")
            
            # Quality distribution
            high_quality = sum(1 for r in successful_results if r['quality_score'] >= 0.8)
            medium_quality = sum(1 for r in successful_results if 0.6 <= r['quality_score'] < 0.8)
            low_quality = sum(1 for r in successful_results if r['quality_score'] < 0.6)
            
            print(f"   Quality Distribution:")
            print(f"     High (≥0.8): {high_quality} files")
            print(f"     Medium (0.6-0.8): {medium_quality} files") 
            print(f"     Low (<0.6): {low_quality} files")
        
        # Test Summary
        print("\n" + "=" * 60)
        success_rate = len(successful_results) / len(results) * 100 if results else 0
        
        if success_rate >= 80:
            print("🎉 Hybrid AI System Test: PASSED")
        elif success_rate >= 60:
            print("⚠️ Hybrid AI System Test: PARTIAL SUCCESS")
        else:
            print("❌ Hybrid AI System Test: FAILED")
        
        print(f"\n📋 Test Summary:")
        print(f"   Files Processed: {len(results)}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   System Status: {'✅ Operational' if success_rate > 0 else '❌ Issues Detected'}")
        
        if successful_results:
            best_result = max(successful_results, key=lambda x: x['quality_score'])
            print(f"   Best Quality: {best_result['quality_score']:.2f} ({best_result['file']})")
        
        print(f"\n🔧 Next Steps:")
        if success_rate < 100:
            print("   - Review failed processing cases")
            print("   - Check AI provider configurations")
            print("   - Validate prompt templates")
        if avg_quality < 0.7:
            print("   - Consider prompt engineering improvements")
            print("   - Review quality assessment thresholds")
        print("   - Monitor system performance in production")
        
        return success_rate >= 60
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print("Full error:")
        traceback.print_exc()
        return False


def test_configuration():
    """Test hybrid system configuration."""
    print("\n🔧 Testing Configuration...")
    
    try:
        from src.utils.config import get_config
        config = get_config()
        
        # Check hybrid configuration
        issues = []
        
        if not hasattr(config, 'ai_providers'):
            issues.append("Missing ai_providers configuration")
        
        if not hasattr(config, 'quality'):
            issues.append("Missing quality configuration")
            
        if hasattr(config, 'processing') and not hasattr(config.processing, 'strategy'):
            issues.append("Missing processing.strategy setting")
        
        # Check prompt templates
        prompt_dir = Path("config/prompts")
        if not prompt_dir.exists():
            issues.append("Missing prompts directory")
        else:
            required_templates = [
                "claude_summary_template.txt",
                "ollama_enhanced_template.txt", 
                "entity_extraction_template.txt"
            ]
            
            for template in required_templates:
                if not (prompt_dir / template).exists():
                    issues.append(f"Missing template: {template}")
        
        if issues:
            print("   ⚠️ Configuration Issues Found:")
            for issue in issues:
                print(f"     - {issue}")
            return False
        else:
            print("   ✅ Configuration looks good")
            return True
            
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False


def main():
    """Run all hybrid system tests."""
    print("🚀 Starting Pensieve Hybrid AI System Tests\n")
    
    # Test 1: Configuration
    config_ok = test_configuration()
    
    # Test 2: Full system (only if config is OK)
    if config_ok:
        system_ok = test_hybrid_system()
    else:
        print("\n❌ Skipping system tests due to configuration issues")
        system_ok = False
    
    # Final summary
    print("\n" + "=" * 80)
    if config_ok and system_ok:
        print("🎉 ALL TESTS PASSED - Hybrid AI System Ready!")
        print("\nTo use the hybrid system:")
        print("1. Set ANTHROPIC_API_KEY environment variable for Claude")
        print("2. Enable Claude in config/settings.yaml: ai_providers.claude.enabled = true")
        print("3. Run: python src/main.py")
    elif config_ok:
        print("⚠️ PARTIAL SUCCESS - Configuration OK, System Issues")
        print("\nCheck the error messages above and:")
        print("1. Verify Ollama is running: ollama serve")
        print("2. Check network connectivity")
        print("3. Review log files for details")
    else:
        print("❌ TESTS FAILED - Configuration Issues")
        print("\nFix configuration issues and re-run tests")
    
    return config_ok and system_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 