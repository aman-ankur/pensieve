"""
Hybrid AI Processor for Pensieve.
Integrates multiple AI providers with intelligent fallback and quality assessment.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .ai_providers import AIProviderManager, ProcessingContext, AIResponse
from .ai_processor import TranscriptParser, ProcessingResult, MeetingMetadata
from ..utils.config import get_config
from ..utils.logger import get_logger, log_performance_metrics


@dataclass
class QualityMetrics:
    """Quality assessment metrics for summaries."""
    technical_terms_count: int = 0
    action_items_count: int = 0
    business_context_score: float = 0.0
    clarity_score: float = 0.0
    overall_score: float = 0.0
    confidence_level: str = "medium"  # low, medium, high
    quality_issues: List[str] = None
    
    def __post_init__(self):
        if self.quality_issues is None:
            self.quality_issues = []


class QualityAssessor:
    """Assesses the quality of generated summaries."""
    
    def __init__(self):
        self.logger = get_logger("quality_assessor")
        self.config = get_config()
    
    def assess_summary_quality(self, summary: str, metadata: MeetingMetadata, provider_used: str) -> QualityMetrics:
        """Assess the quality of a generated summary."""
        try:
            metrics = QualityMetrics()
            
            # Count technical terms
            metrics.technical_terms_count = self._count_technical_terms(summary)
            
            # Count action items
            metrics.action_items_count = self._count_action_items(summary)
            
            # Assess business context
            metrics.business_context_score = self._assess_business_context(summary, metadata)
            
            # Assess clarity
            metrics.clarity_score = self._assess_clarity(summary)
            
            # Calculate overall score
            metrics.overall_score = self._calculate_overall_score(metrics)
            
            # Determine confidence level
            metrics.confidence_level = self._determine_confidence(metrics, provider_used)
            
            # Identify quality issues
            metrics.quality_issues = self._identify_quality_issues(summary, metrics, metadata)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return QualityMetrics(
                overall_score=0.5,
                confidence_level="low",
                quality_issues=["Quality assessment failed"]
            )
    
    def _count_technical_terms(self, summary: str) -> int:
        """Count technical terms in the summary."""
        technical_indicators = [
            "api", "service", "system", "architecture", "framework",
            "database", "server", "client", "endpoint", "integration",
            "deployment", "authentication", "authorization", "oauth",
            "microservices", "rest", "graphql", "json", "xml",
            "kubernetes", "docker", "aws", "azure", "gcp",
            "python", "java", "javascript", "typescript", "react",
            "node", "express", "spring", "django", "flask"
        ]
        
        summary_lower = summary.lower()
        count = sum(1 for term in technical_indicators if term in summary_lower)
        
        # Look for specific patterns that indicate technical content
        if "implementation" in summary_lower:
            count += 1
        if "design pattern" in summary_lower:
            count += 1
        if any(word in summary_lower for word in ["multiplier", "cullinson", "booking"]):
            count += 2  # Domain-specific technical terms
            
        return count
    
    def _count_action_items(self, summary: str) -> int:
        """Count action items in the summary."""
        # Look for action item patterns
        action_patterns = [
            "- [ ]", "- [x]", "TODO:", "Action:", "Follow-up:",
            "@" + "person", "Due:", "Timeline:", "Next step"
        ]
        
        count = 0
        lines = summary.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(pattern.lower() in line_lower for pattern in action_patterns):
                count += 1
            # Look for @mentions
            if "@" in line and any(word in line_lower for word in ["due", "timeline", "task", "action"]):
                count += 1
                
        return count
    
    def _assess_business_context(self, summary: str, metadata: MeetingMetadata) -> float:
        """Assess how well the summary captures business context."""
        summary_lower = summary.lower()
        score = 0.0
        
        # Check for business context indicators
        business_indicators = [
            "revenue", "customer", "product", "market", "business",
            "strategy", "growth", "impact", "value", "roi",
            "profit", "cost", "budget", "investment", "kpi"
        ]
        
        found_indicators = sum(1 for term in business_indicators if term in summary_lower)
        score += min(found_indicators / 5.0, 1.0) * 0.4  # Up to 40% for business terms
        
        # Check for specific business context (domain-specific)
        domain_terms = ["flights", "booking", "travel", "hotel", "ancillary"]
        found_domain = sum(1 for term in domain_terms if term in summary_lower)
        score += min(found_domain / 2.0, 1.0) * 0.3  # Up to 30% for domain context
        
        # Check for strategic elements
        if any(word in summary_lower for word in ["strategy", "roadmap", "priority", "objective"]):
            score += 0.3  # 30% for strategic content
            
        return min(score, 1.0)
    
    def _assess_clarity(self, summary: str) -> float:
        """Assess the clarity and structure of the summary."""
        score = 0.0
        
        # Check for structured format
        if "# " in summary or "## " in summary:
            score += 0.3  # 30% for headers
            
        # Check for bullet points or lists
        if "- " in summary or "* " in summary:
            score += 0.2  # 20% for lists
            
        # Check for clear sections
        sections = ["business", "technical", "action", "decision", "challenge"]
        found_sections = sum(1 for section in sections if section in summary.lower())
        score += min(found_sections / len(sections), 1.0) * 0.3  # Up to 30% for sections
        
        # Check for appropriate length
        if 200 <= len(summary) <= 3000:
            score += 0.2  # 20% for appropriate length
            
        return min(score, 1.0)
    
    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score."""
        config = self.config.quality.scoring
        
        # Normalize scores
        tech_score = min(metrics.technical_terms_count / 5.0, 1.0)  # Expect ~5 technical terms
        action_score = min(metrics.action_items_count / 3.0, 1.0)   # Expect ~3 action items
        
        # Weighted combination
        overall = (
            tech_score * config.technical_content +
            action_score * config.action_items +
            metrics.business_context_score * config.business_context +
            metrics.clarity_score * config.clarity
        )
        
        return min(overall, 1.0)
    
    def _determine_confidence(self, metrics: QualityMetrics, provider_used: str) -> str:
        """Determine confidence level based on metrics and provider."""
        if metrics.overall_score >= 0.8:
            return "high"
        elif metrics.overall_score >= 0.6:
            return "medium"
        elif provider_used == "claude" and metrics.overall_score >= 0.4:
            return "medium"  # Claude gets benefit of doubt
        else:
            return "low"
    
    def _identify_quality_issues(self, summary: str, metrics: QualityMetrics, metadata: MeetingMetadata) -> List[str]:
        """Identify specific quality issues."""
        issues = []
        
        # Check minimum requirements
        config = self.config.quality
        
        if len(summary) < config.min_summary_length:
            issues.append(f"Summary too short ({len(summary)} chars, minimum {config.min_summary_length})")
        
        if metrics.technical_terms_count < config.min_technical_terms:
            issues.append(f"Insufficient technical content ({metrics.technical_terms_count} terms, minimum {config.min_technical_terms})")
        
        if metrics.action_items_count < config.min_action_items:
            issues.append(f"No clear action items identified")
        
        # Check for generic content
        generic_phrases = [
            "the team discussed", "improving collaboration", "better communication",
            "working together", "moving forward", "next steps"
        ]
        
        summary_lower = summary.lower()
        found_generic = [phrase for phrase in generic_phrases if phrase in summary_lower]
        if found_generic:
            issues.append(f"Contains generic phrases: {', '.join(found_generic[:2])}")
        
        # Check for missing specific details
        if not any(name in summary for name in metadata.participants if len(name) > 3):
            issues.append("Missing specific participant references")
        
        return issues


class HybridAIProcessor:
    """
    Enhanced AI processor that uses multiple providers with intelligent fallback.
    Integrates with existing Pensieve architecture while adding hybrid capabilities.
    """
    
    def __init__(self):
        self.logger = get_logger("hybrid_ai_processor")
        self.config = get_config()
        
        # Initialize components
        self.transcript_parser = TranscriptParser()
        self.ai_manager = AIProviderManager()
        self.quality_assessor = QualityAssessor()
        
        # Load prompt templates
        self._load_prompt_templates()
        
        self.logger.info("Hybrid AI Processor initialized")
    
    def _load_prompt_templates(self) -> None:
        """Load prompt templates for different providers."""
        self.prompt_templates = {}
        
        try:
            # Claude template
            claude_template_path = Path("config/prompts/claude_summary_template.txt")
            if claude_template_path.exists():
                with open(claude_template_path, 'r') as f:
                    self.prompt_templates['claude'] = f.read()
            
            # Enhanced Ollama template
            ollama_template_path = Path("config/prompts/ollama_enhanced_template.txt")
            if ollama_template_path.exists():
                with open(ollama_template_path, 'r') as f:
                    self.prompt_templates['ollama'] = f.read()
            
            # Entity extraction template
            entity_template_path = Path("config/prompts/entity_extraction_template.txt")
            if entity_template_path.exists():
                with open(entity_template_path, 'r') as f:
                    self.prompt_templates['entity_extraction'] = f.read()
            
            # Fallback to original template
            if not self.prompt_templates:
                fallback_path = Path("config/prompts/summary_template.txt")
                if fallback_path.exists():
                    with open(fallback_path, 'r') as f:
                        template = f.read()
                        self.prompt_templates['fallback'] = template
                        self.prompt_templates['claude'] = template
                        self.prompt_templates['ollama'] = template
            
            self.logger.info(f"Loaded {len(self.prompt_templates)} prompt templates")
            
        except Exception as e:
            self.logger.error(f"Failed to load prompt templates: {e}")
            # Set minimal fallback templates
            self.prompt_templates = {
                'claude': "Analyze this meeting transcript and create a detailed summary.",
                'ollama': "Analyze this meeting transcript and create a detailed summary.",
                'fallback': "Analyze this meeting transcript and create a detailed summary."
            }
    
    def process_transcript(self, file_path: Path) -> ProcessingResult:
        """
        Process a transcript using the hybrid AI strategy.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            ProcessingResult with enhanced metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing transcript: {file_path.name}")
            
            # Step 1: Parse transcript and extract metadata
            transcript_content, metadata = self.transcript_parser.parse_transcript(file_path)
            
            # Step 2: Create processing context
            context = ProcessingContext(
                meeting_title=metadata.title,
                meeting_date=metadata.date,
                participants=metadata.participants,
                meeting_type=metadata.meeting_type,
                file_size=metadata.file_size,
                estimated_tokens=metadata.file_size // 4,  # Rough estimate
                requires_chunking=metadata.file_size > 8000  # 8KB threshold
            )
            
            # Step 3: Select appropriate prompt template and provider
            prompt_template = self._select_prompt_template(context)
            formatted_prompt = self._format_prompt(prompt_template, metadata)
            
            # Step 4: Process with AI provider manager
            ai_response = self.ai_manager.process_with_fallback(
                formatted_prompt, transcript_content, context
            )
            
            if not ai_response.success:
                return ProcessingResult(
                    success=False,
                    error=f"AI processing failed: {ai_response.error}",
                    processing_time=time.time() - start_time
                )
            
            # Step 5: Quality assessment
            quality_metrics = self.quality_assessor.assess_summary_quality(
                ai_response.content, metadata, ai_response.provider_used
            )
            
            # Step 6: Create enhanced result
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                success=True,
                summary=ai_response.content,
                metadata=metadata,
                processing_time=processing_time,
                model_used=ai_response.model_used,
                chunks_processed=getattr(ai_response, 'chunks_processed', 0)
            )
            
            # Add hybrid-specific metadata
            result.ai_provider_used = ai_response.provider_used
            result.quality_metrics = quality_metrics
            result.processing_strategy = "hybrid"
            result.provider_processing_time = ai_response.processing_time
            result.tokens_used = ai_response.tokens_used
            result.provider_metadata = ai_response.metadata
            
            # Log comprehensive metrics
            log_performance_metrics(
                "hybrid_processing",
                processing_time,
                success=True,
                provider=ai_response.provider_used,
                model=ai_response.model_used,
                quality_score=quality_metrics.overall_score,
                confidence=quality_metrics.confidence_level,
                file_size=metadata.file_size,
                participants=len(metadata.participants)
            )
            
            self.logger.info(
                f"Successfully processed with {ai_response.provider_used} "
                f"(quality: {quality_metrics.overall_score:.2f}, "
                f"confidence: {quality_metrics.confidence_level})"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Hybrid processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            log_performance_metrics(
                "hybrid_processing", 
                processing_time, 
                success=False
            )
            
            return ProcessingResult(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def _select_prompt_template(self, context: ProcessingContext) -> str:
        """Select the appropriate prompt template based on context."""
        # Check for provider preference based on meeting type
        meeting_config = getattr(self.config.meeting_types, context.meeting_type.lower().replace(' ', '_'), None)
        
        if meeting_config and hasattr(meeting_config, 'preferred_provider'):
            preferred = meeting_config.preferred_provider
            if preferred in self.prompt_templates:
                return self.prompt_templates[preferred]
        
        # Default selection logic
        if 'claude' in self.prompt_templates:
            return self.prompt_templates['claude']
        elif 'ollama' in self.prompt_templates:
            return self.prompt_templates['ollama']
        else:
            return self.prompt_templates.get('fallback', 
                "Analyze this meeting transcript and create a detailed summary.")
    
    def _format_prompt(self, template: str, metadata: MeetingMetadata) -> str:
        """Format prompt template with meeting metadata."""
        try:
            return template.format(
                meeting_title=metadata.title,
                meeting_date=metadata.date,
                duration=metadata.duration,
                participants=", ".join(metadata.participants),
                meeting_type=metadata.meeting_type
            )
        except KeyError as e:
            self.logger.warning(f"Template formatting failed for key {e}, using basic template")
            return template
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the hybrid processing system."""
        return {
            "ai_providers": self.ai_manager.get_provider_status(),
            "prompt_templates": list(self.prompt_templates.keys()),
            "quality_thresholds": {
                "min_summary_length": self.config.quality.min_summary_length,
                "min_technical_terms": self.config.quality.min_technical_terms,
                "min_action_items": self.config.quality.min_action_items
            },
            "processing_strategy": self.config.processing.strategy,
            "features": {
                "cloud_fallback": self.config.features.cloud_fallback,
                "quality_assessment": self.config.features.quality_assessment,
                "adaptive_chunking": self.config.features.adaptive_chunking
            }
        }
    
    def regenerate_with_different_provider(self, file_path: Path, provider_name: str) -> ProcessingResult:
        """Regenerate summary using a specific provider (for testing/comparison)."""
        try:
            # Parse transcript
            transcript_content, metadata = self.transcript_parser.parse_transcript(file_path)
            
            # Create context
            context = ProcessingContext(
                meeting_title=metadata.title,
                meeting_date=metadata.date,
                participants=metadata.participants,
                meeting_type=metadata.meeting_type,
                file_size=metadata.file_size
            )
            
            # Get specific provider
            provider = None
            for p in self.ai_manager.providers:
                if p.config.name == provider_name:
                    provider = p
                    break
            
            if not provider:
                return ProcessingResult(
                    success=False,
                    error=f"Provider {provider_name} not found"
                )
            
            if not provider.is_available():
                return ProcessingResult(
                    success=False,
                    error=f"Provider {provider_name} not available"
                )
            
            # Format prompt for this provider
            template = self.prompt_templates.get(provider_name, self.prompt_templates.get('fallback'))
            formatted_prompt = self._format_prompt(template, metadata)
            
            # Process with specific provider
            ai_response = provider.generate_summary(formatted_prompt, transcript_content, context)
            
            if not ai_response.success:
                return ProcessingResult(
                    success=False,
                    error=ai_response.error
                )
            
            # Assess quality
            quality_metrics = self.quality_assessor.assess_summary_quality(
                ai_response.content, metadata, provider_name
            )
            
            result = ProcessingResult(
                success=True,
                summary=ai_response.content,
                metadata=metadata,
                processing_time=ai_response.processing_time,
                model_used=ai_response.model_used
            )
            
            result.ai_provider_used = provider_name
            result.quality_metrics = quality_metrics
            result.processing_strategy = f"manual_{provider_name}"
            
            return result
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"Regeneration failed: {str(e)}"
            ) 