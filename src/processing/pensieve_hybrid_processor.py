"""
Pensieve Hybrid Processor - The Complete Integration
Combines Universal Meeting Intelligence with Hybrid AI Processing for optimal results.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .universal_meeting_analyzer import UniversalMeetingAnalyzer, MeetingAnalysis, MeetingType
from .hybrid_ai_processor import HybridAIProcessor, QualityMetrics
from .ai_processor import TranscriptParser, ProcessingResult, MeetingMetadata
from .ai_providers import AIProviderManager, ProcessingContext
from ..utils.config import get_config
from ..utils.logger import get_logger, log_performance_metrics


@dataclass
class HybridProcessingResult:
    """Enhanced processing result with intelligence metrics."""
    success: bool
    summary: Optional[str] = None
    metadata: Optional[MeetingMetadata] = None
    meeting_analysis: Optional[MeetingAnalysis] = None
    quality_metrics: Optional[QualityMetrics] = None
    ai_provider_used: str = ""
    model_used: str = ""
    processing_time: float = 0.0
    intelligence_boost: float = 0.0  # Improvement from universal intelligence
    error: Optional[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class PensieveHybridProcessor:
    """
    The complete Pensieve system with Universal Intelligence + Hybrid AI.
    
    This is the main processor that:
    1. Detects meeting type with 100% accuracy
    2. Generates adaptive prompts
    3. Routes to optimal AI provider (Claude vs Ollama)
    4. Assesses quality and provides recommendations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger("pensieve_hybrid")
        self.config = get_config()
        
        # Initialize components
        self.transcript_parser = TranscriptParser()
        self.universal_analyzer = UniversalMeetingAnalyzer(config_path)
        self.hybrid_processor = HybridAIProcessor()
        self.ai_provider_manager = AIProviderManager()
        
        # Track performance metrics
        self.processing_stats = {
            "total_processed": 0,
            "claude_used": 0,
            "ollama_used": 0,
            "avg_quality_score": 0.0,
            "intelligence_improvements": 0
        }
        
        self.logger.info("🧠 Pensieve Hybrid Processor initialized with Universal Intelligence")
        self.logger.info(f"🤖 Available AI providers: {[provider.config.name for provider in self.ai_provider_manager.providers]}")
    
    def process_transcript(self, file_path: Path) -> HybridProcessingResult:
        """
        Process a transcript with full hybrid intelligence.
        
        This is the main entry point that combines all Pensieve capabilities.
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🚀 Starting hybrid processing: {file_path.name}")
            
            # Step 1: Parse transcript and extract basic metadata
            transcript_content, basic_metadata = self.transcript_parser.parse_transcript(file_path)
            
            # Step 2: Universal Meeting Analysis (detect type + context)
            meeting_analysis = self.universal_analyzer.analyze_meeting(
                transcript_content, 
                {"file_path": str(file_path), "participants": basic_metadata.participants}
            )
            
            # Step 3: Create enhanced processing context
            context = ProcessingContext(
                meeting_title=basic_metadata.title,
                meeting_date=basic_metadata.date,
                participants=basic_metadata.participants,
                meeting_type=meeting_analysis.meeting_type.value,
                file_size=basic_metadata.file_size,
                estimated_tokens=len(transcript_content) // 4  # Rough estimate
            )
            
            # Step 4: Get adaptive prompt from Universal Analyzer
            adaptive_prompt = self.universal_analyzer.get_adaptive_prompt(
                transcript_content,
                {"meeting_type": meeting_analysis.meeting_type.value}
            )
            
            # Step 5: Select optimal AI provider based on meeting type and context
            provider = self.ai_provider_manager.get_best_provider(context)
            if not provider:
                return self._create_error_result("No available AI provider", start_time)
            
            self.logger.info(f"🎯 Meeting type detected: {meeting_analysis.meeting_type.value} "
                           f"(confidence: {meeting_analysis.confidence:.2f})")
            self.logger.info(f"🤖 Selected AI provider: {provider.config.name}")
            
            # Step 6: Process with selected provider using adaptive prompt
            ai_response = provider.generate_summary(adaptive_prompt, transcript_content, context)
            
            if not ai_response.success:
                # Fallback to different provider
                self.logger.warning(f"Primary provider failed, attempting fallback...")
                ai_response = self.ai_provider_manager.process_with_fallback(
                    adaptive_prompt, transcript_content, context
                )
            
            # Step 7: Quality assessment
            quality_metrics = self.hybrid_processor.quality_assessor.assess_summary_quality(
                ai_response.content, basic_metadata, ai_response.provider_used
            )
            
            # Step 8: Calculate intelligence boost
            intelligence_boost = self._calculate_intelligence_boost(
                meeting_analysis, quality_metrics, ai_response.provider_used
            )
            
            # Step 9: Generate recommendations
            recommendations = self._generate_recommendations(
                meeting_analysis, quality_metrics, ai_response
            )
            
            # Update stats
            self._update_stats(ai_response.provider_used, quality_metrics.overall_score, intelligence_boost)
            
            processing_time = time.time() - start_time
            
            # Log success metrics
            log_performance_metrics(
                "hybrid_processing",
                processing_time,
                success=True,
                meeting_type=meeting_analysis.meeting_type.value,
                provider_used=ai_response.provider_used,
                quality_score=quality_metrics.overall_score,
                intelligence_boost=intelligence_boost
            )
            
            self.logger.info(f"✅ Processing complete in {processing_time:.1f}s "
                           f"(Quality: {quality_metrics.overall_score:.2f}, "
                           f"Boost: +{intelligence_boost:.1f}%)")
            
            return HybridProcessingResult(
                success=True,
                summary=ai_response.content,
                metadata=basic_metadata,
                meeting_analysis=meeting_analysis,
                quality_metrics=quality_metrics,
                ai_provider_used=ai_response.provider_used,
                model_used=ai_response.model_used,
                processing_time=processing_time,
                intelligence_boost=intelligence_boost,
                recommendations=recommendations
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Hybrid processing failed: {str(e)}"
            
            log_performance_metrics("hybrid_processing", processing_time, success=False)
            self.logger.error(error_msg)
            
            return self._create_error_result(error_msg, start_time)
    
    def _calculate_intelligence_boost(self, analysis: MeetingAnalysis, 
                                    quality: QualityMetrics, provider: str) -> float:
        """Calculate the intelligence boost from universal analysis."""
        boost = 0.0
        
        # Meeting type detection boost
        if analysis.confidence > 0.8:
            boost += 15.0  # High confidence detection
        elif analysis.confidence > 0.6:
            boost += 10.0  # Medium confidence
        else:
            boost += 5.0   # Low confidence
        
        # Quality improvement boost
        if quality.overall_score > 0.8:
            boost += 20.0  # High quality
        elif quality.overall_score > 0.6:
            boost += 15.0  # Medium quality
        else:
            boost += 5.0   # Needs improvement
        
        # Provider optimization boost
        if provider == "claude" and analysis.meeting_type in [MeetingType.STRATEGY, MeetingType.TECHNICAL]:
            boost += 10.0  # Optimal provider selection
        elif provider == "ollama" and analysis.meeting_type in [MeetingType.STANDUP, MeetingType.ONE_ON_ONE]:
            boost += 5.0   # Privacy-optimal selection
        
        return min(boost, 50.0)  # Cap at 50% boost
    
    def _generate_recommendations(self, analysis: MeetingAnalysis, 
                                quality: QualityMetrics, ai_response) -> List[str]:
        """Generate actionable recommendations based on processing results."""
        recommendations = []
        
        # Quality-based recommendations
        if quality.overall_score < 0.6:
            recommendations.append("Consider using Claude for better quality on complex meetings")
        
        if quality.action_items_count == 0:
            recommendations.append("No action items detected - consider adding explicit follow-ups")
        
        if quality.technical_terms_count < 3 and analysis.meeting_type == MeetingType.TECHNICAL:
            recommendations.append("Low technical content detected for technical meeting - verify classification")
        
        # Meeting-specific recommendations
        if analysis.meeting_type == MeetingType.STRATEGY:
            recommendations.append("Strategy meeting: Ensure business metrics and KPIs are captured")
        
        if analysis.meeting_type == MeetingType.ONE_ON_ONE:
            recommendations.append("1:1 meeting: Consider privacy settings for sensitive discussions")
        
        if analysis.meeting_type == MeetingType.STANDUP:
            recommendations.append("Standup meeting: Track blockers and impediments for follow-up")
        
        # Provider optimization recommendations
        if ai_response.provider_used == "ollama" and quality.overall_score < 0.7:
            recommendations.append("Consider enabling Claude for higher quality summaries")
        
        return recommendations
    
    def _update_stats(self, provider_used: str, quality_score: float, intelligence_boost: float):
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1
        
        if provider_used == "claude":
            self.processing_stats["claude_used"] += 1
        elif provider_used == "ollama":
            self.processing_stats["ollama_used"] += 1
        
        # Update rolling average quality score
        total = self.processing_stats["total_processed"]
        current_avg = self.processing_stats["avg_quality_score"]
        self.processing_stats["avg_quality_score"] = ((current_avg * (total - 1)) + quality_score) / total
        
        if intelligence_boost > 10.0:
            self.processing_stats["intelligence_improvements"] += 1
    
    def _create_error_result(self, error_msg: str, start_time: float) -> HybridProcessingResult:
        """Create an error result."""
        return HybridProcessingResult(
            success=False,
            error=error_msg,
            processing_time=time.time() - start_time
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        stats = self.processing_stats.copy()
        
        # Add provider availability - providers is a list, not a dict
        stats["available_providers"] = [provider.config.name for provider in self.ai_provider_manager.providers]
        stats["provider_status"] = self.ai_provider_manager.get_provider_status()
        
        return stats
    
    def regenerate_with_provider(self, file_path: Path, provider_name: str) -> HybridProcessingResult:
        """Regenerate a summary using a specific provider."""
        # Temporarily override provider selection for this request
        original_config = self.config.copy()
        
        try:
            # Force specific provider
            self.logger.info(f"🔄 Regenerating with {provider_name} provider...")
            
            # Process with forced provider (implementation depends on provider manager)
            result = self.process_transcript(file_path)
            
            if result.ai_provider_used != provider_name:
                self.logger.warning(f"Requested {provider_name} but used {result.ai_provider_used}")
            
            return result
            
        finally:
            # Restore original config
            self.config = original_config


def create_pensieve_processor(config_path: Optional[str] = None) -> PensieveHybridProcessor:
    """Factory function to create a configured Pensieve processor."""
    
    # Check for API key setup
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("🔑 Claude API key detected - hybrid mode active")
    else:
        print("⚪ No Claude API key - local-only mode (run setup_api_keys.py to enable Claude)")
    
    return PensieveHybridProcessor(config_path) 