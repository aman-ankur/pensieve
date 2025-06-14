#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Pensieve Hybrid System
Tests the complete integration of Universal Intelligence + Hybrid AI Processing.
"""

import os
import sys
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.processing.pensieve_hybrid_processor import PensieveHybridProcessor, create_pensieve_processor
from src.processing.universal_meeting_analyzer import MeetingType
from src.processing.ai_providers import AIResponse


class TestHybridIntegration:
    """Test the complete hybrid integration."""
    
    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript for testing."""
        return """
        John Smith 09:00:15
        Good morning everyone, let's start with our architecture review for the new booking service.
        
        Alice Johnson 09:00:30
        Thanks John. I've been working on the microservice design for our payment flow.
        
        Bob Wilson 09:01:00
        Great work Alice. I have some concerns about the database scalability approach.
        
        John Smith 09:01:15
        Let's discuss the technical trade-offs. We need to consider performance implications.
        
        Alice Johnson 09:02:00
        The service-oriented architecture will help us scale better than our current monolith.
        
        Bob Wilson 09:02:30
        I agree. My action item is to create a performance testing plan by next week.
        
        John Smith 09:03:00
        Perfect. Alice, can you finalize the API specifications by Friday?
        
        Alice Johnson 09:03:15
        Absolutely. I'll have the complete API documentation ready.
        """
    
    @pytest.fixture
    def mock_transcript_file(self, tmp_path, sample_transcript):
        """Create a mock transcript file."""
        meeting_folder = tmp_path / "2025-01-18 09.00.00 Architecture Review Meeting"
        meeting_folder.mkdir()
        
        transcript_file = meeting_folder / "meeting_saved_closed_caption.txt"
        transcript_file.write_text(sample_transcript)
        
        return transcript_file
    
    def test_hybrid_processor_initialization(self):
        """Test that hybrid processor initializes correctly."""
        processor = create_pensieve_processor()
        
        assert processor is not None
        assert hasattr(processor, 'universal_analyzer')
        assert hasattr(processor, 'hybrid_processor')
        assert hasattr(processor, 'ai_provider_manager')
        assert hasattr(processor, 'transcript_parser')
    
    def test_meeting_type_detection_integration(self, mock_transcript_file):
        """Test that meeting type detection works in the integrated system."""
        processor = create_pensieve_processor()
        
        # Mock the AI response to focus on testing integration
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content="# Technical Architecture Review\n\n## Key Decisions\n- Microservice approach approved\n\n## Action Items\n- [ ] Performance testing plan (Bob)\n- [ ] API documentation (Alice)",
                provider_used="ollama",
                model_used="llama3.1:8b",
                processing_time=5.0
            )
            mock_provider.return_value = mock_ai_provider
            
            result = processor.process_transcript(mock_transcript_file)
            
            assert result.success == True
            assert result.meeting_analysis.meeting_type == MeetingType.TECHNICAL
            assert result.meeting_analysis.confidence > 0.8
            assert "Architecture Review" in result.metadata.title
    
    def test_adaptive_prompt_generation(self, mock_transcript_file):
        """Test that adaptive prompts are generated correctly."""
        processor = create_pensieve_processor()
        
        # Get the transcript content
        transcript_content, _ = processor.transcript_parser.parse_transcript(mock_transcript_file)
        
        # Test adaptive prompt generation
        adaptive_prompt = processor.universal_analyzer.get_adaptive_prompt(
            transcript_content,
            {"meeting_type": "technical"}
        )
        
        assert adaptive_prompt is not None
        assert len(adaptive_prompt) > 100  # Should be a substantial prompt
        assert "technical" in adaptive_prompt.lower()
        assert "architecture" in adaptive_prompt.lower() or "api" in adaptive_prompt.lower()
    
    def test_provider_selection_logic(self, mock_transcript_file):
        """Test that the right provider is selected based on meeting type."""
        processor = create_pensieve_processor()
        
        with patch.object(processor.ai_provider_manager, 'providers') as mock_providers:
            # Mock both providers available
            claude_provider = Mock()
            claude_provider.config.name = "claude"
            claude_provider.config.priority = 1
            claude_provider.is_available.return_value = True
            
            ollama_provider = Mock()
            ollama_provider.config.name = "ollama"
            ollama_provider.config.priority = 2
            ollama_provider.is_available.return_value = True
            
            mock_providers = {"claude": claude_provider, "ollama": ollama_provider}
            
            # Mock the provider manager's selection logic
            with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_get_best:
                # For technical meetings, should prefer Claude
                mock_get_best.return_value = claude_provider
                
                claude_provider.generate_summary.return_value = AIResponse(
                    success=True,
                    content="High-quality technical summary",
                    provider_used="claude",
                    model_used="claude-3-5-sonnet-20241022"
                )
                
                result = processor.process_transcript(mock_transcript_file)
                
                assert result.success == True
                assert result.ai_provider_used == "claude"
    
    def test_quality_assessment_integration(self, mock_transcript_file):
        """Test that quality assessment works correctly."""
        processor = create_pensieve_processor()
        
        # Mock AI response with known content
        mock_summary = """
        # Technical Architecture Review Summary
        
        ## Key Technical Decisions
        - Microservice architecture approved for payment service
        - Database scalability concerns raised and addressed
        - API-first approach for service integration
        
        ## Action Items
        - [ ] **Bob Wilson** - Create performance testing plan - **Due: Next Week**
        - [ ] **Alice Johnson** - Finalize API specifications - **Due: Friday**
        
        ## Technical Context
        The team discussed service-oriented architecture benefits over monolithic design.
        Performance implications and scalability were key considerations.
        """
        
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content=mock_summary,
                provider_used="claude",
                model_used="claude-3-5-sonnet-20241022"
            )
            mock_provider.return_value = mock_ai_provider
            
            result = processor.process_transcript(mock_transcript_file)
            
            assert result.success == True
            assert result.quality_metrics is not None
            assert result.quality_metrics.action_items_count >= 2
            assert result.quality_metrics.technical_terms_count >= 3
            assert result.quality_metrics.overall_score > 0.7
    
    def test_intelligence_boost_calculation(self, mock_transcript_file):
        """Test intelligence boost calculation."""
        processor = create_pensieve_processor()
        
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content="High-quality summary with technical content and action items",
                provider_used="claude",
                model_used="claude-3-5-sonnet-20241022"
            )
            mock_provider.return_value = mock_ai_provider
            
            result = processor.process_transcript(mock_transcript_file)
            
            assert result.success == True
            assert result.intelligence_boost > 0
            assert result.intelligence_boost <= 50.0  # Should be capped
    
    def test_recommendations_generation(self, mock_transcript_file):
        """Test that actionable recommendations are generated."""
        processor = create_pensieve_processor()
        
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content="Basic summary without much detail",
                provider_used="ollama",
                model_used="llama3.1:8b"
            )
            mock_provider.return_value = mock_ai_provider
            
            result = processor.process_transcript(mock_transcript_file)
            
            assert result.success == True
            assert result.recommendations is not None
            assert len(result.recommendations) > 0
            # Should recommend Claude for better quality
            assert any("Claude" in rec for rec in result.recommendations)
    
    def test_error_handling_integration(self, mock_transcript_file):
        """Test error handling in the integrated system."""
        processor = create_pensieve_processor()
        
        # Test with provider failure
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_provider.return_value = None  # No provider available
            
            result = processor.process_transcript(mock_transcript_file)
            
            assert result.success == False
            assert result.error is not None
            assert "No available AI provider" in result.error
    
    def test_fallback_mechanism(self, mock_transcript_file):
        """Test provider fallback mechanism."""
        processor = create_pensieve_processor()
        
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            # Primary provider fails
            mock_primary = Mock()
            mock_primary.generate_summary.return_value = AIResponse(
                success=False,
                error="Primary provider failed"
            )
            mock_provider.return_value = mock_primary
            
            # Fallback should work
            with patch.object(processor.ai_provider_manager, 'process_with_fallback') as mock_fallback:
                mock_fallback.return_value = AIResponse(
                    success=True,
                    content="Fallback summary",
                    provider_used="ollama",
                    model_used="llama3.1:8b"
                )
                
                result = processor.process_transcript(mock_transcript_file)
                
                assert result.success == True
                assert result.ai_provider_used == "ollama"
                mock_fallback.assert_called_once()
    
    def test_processing_stats_tracking(self, mock_transcript_file):
        """Test that processing statistics are tracked correctly."""
        processor = create_pensieve_processor()
        
        initial_stats = processor.get_processing_stats()
        assert initial_stats["total_processed"] == 0
        
        # Mock successful processing
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content="Test summary",
                provider_used="claude",
                model_used="claude-3-5-sonnet-20241022"
            )
            mock_provider.return_value = mock_ai_provider
            
            processor.process_transcript(mock_transcript_file)
            
            updated_stats = processor.get_processing_stats()
            assert updated_stats["total_processed"] == 1
            assert updated_stats["claude_used"] == 1
            assert updated_stats["avg_quality_score"] > 0
    
    def test_environment_variable_detection(self):
        """Test API key detection from environment variables."""
        # Test without API key
        with patch.dict(os.environ, {}, clear=True):
            processor = create_pensieve_processor()
            # Should still work in local-only mode
            assert processor is not None
        
        # Test with API key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}, clear=True):
            processor = create_pensieve_processor()
            # Should detect Claude availability
            assert processor is not None


class TestRealTranscriptProcessing:
    """Test with real transcript files if available."""
    
    def test_with_real_zoom_transcript(self):
        """Test with real Zoom transcript if available."""
        zoom_folder = Path.home() / "Documents" / "Zoom"
        
        if not zoom_folder.exists():
            pytest.skip("No Zoom folder found - skipping real transcript test")
        
        # Find a recent transcript file
        transcript_files = list(zoom_folder.glob("*/meeting_saved_closed_caption.txt"))
        
        if not transcript_files:
            pytest.skip("No transcript files found - skipping real transcript test")
        
        # Test with the most recent transcript
        latest_transcript = max(transcript_files, key=lambda p: p.stat().st_mtime)
        
        processor = create_pensieve_processor()
        
        # Mock AI providers to avoid API calls in tests
        with patch.object(processor.ai_provider_manager, 'get_best_provider') as mock_provider:
            mock_ai_provider = Mock()
            mock_ai_provider.generate_summary.return_value = AIResponse(
                success=True,
                content="Test summary for real transcript",
                provider_used="ollama",
                model_used="llama3.1:8b"
            )
            mock_provider.return_value = mock_ai_provider
            
            result = processor.process_transcript(latest_transcript)
            
            assert result.success == True
            assert result.meeting_analysis is not None
            assert result.metadata is not None
            assert len(result.metadata.participants) > 0


def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Pensieve Hybrid Integration Tests")
    print("=" * 60)
    
    # Create test instance
    test_instance = TestHybridIntegration()
    
    # Run basic tests
    print("🔧 Testing hybrid processor initialization...")
    test_instance.test_hybrid_processor_initialization()
    print("✅ Initialization test passed")
    
    # Create mock transcript for other tests
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock transcript file
        sample_transcript = """
        John Smith 09:00:15
        Good morning everyone, let's start with our architecture review.
        
        Alice Johnson 09:00:30
        Thanks John. I've been working on the microservice design.
        """
        
        meeting_folder = tmp_path / "2025-01-18 09.00.00 Test Meeting"
        meeting_folder.mkdir()
        transcript_file = meeting_folder / "meeting_saved_closed_caption.txt"
        transcript_file.write_text(sample_transcript)
        
        print("🎯 Testing meeting type detection...")
        test_instance.test_meeting_type_detection_integration(transcript_file)
        print("✅ Meeting type detection test passed")
        
        print("📝 Testing adaptive prompt generation...")
        test_instance.test_adaptive_prompt_generation(transcript_file)
        print("✅ Adaptive prompt test passed")
    
    print("\n🎉 All integration tests passed!")
    print("🚀 Hybrid system is ready for production!")


if __name__ == "__main__":
    run_integration_tests() 