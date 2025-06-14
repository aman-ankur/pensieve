"""
Abstract AI Provider system for Pensieve.
Supports multiple AI services with consistent interface and fallback mechanisms.
"""

import json
import os
import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..utils.config import get_config
from ..utils.logger import get_logger, log_performance_metrics


class AIProviderType(Enum):
    """Types of AI providers."""
    CLAUDE = "claude"
    OLLAMA = "ollama" 
    OPENAI = "openai"  # Future
    GEMINI = "gemini"  # Future


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""
    name: str
    provider_type: AIProviderType
    model_name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.1
    timeout: int = 120
    enabled: bool = True
    priority: int = 1  # Lower = higher priority


@dataclass
class ProcessingContext:
    """Context information for AI processing."""
    meeting_title: str
    meeting_date: str
    participants: List[str]
    meeting_type: str
    file_size: int
    estimated_tokens: Optional[int] = None
    requires_chunking: bool = False
    

@dataclass
class AIResponse:
    """Response from an AI provider."""
    success: bool
    content: Optional[str] = None
    provider_used: str = ""
    model_used: str = ""
    processing_time: float = 0.0
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.logger = get_logger(f"ai_provider_{config.name}")
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the provider (setup connections, validate config, etc.)."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and healthy."""
        pass
    
    @abstractmethod
    def supports_full_transcript(self, context: ProcessingContext) -> bool:
        """Check if the provider can handle the full transcript without chunking."""
        pass
    
    @abstractmethod
    def generate_summary(self, prompt: str, transcript: str, context: ProcessingContext) -> AIResponse:
        """Generate a summary using the provider."""
        pass
    
    @abstractmethod
    def extract_entities(self, transcript: str, context: ProcessingContext) -> AIResponse:
        """Extract entities/keywords from transcript (for two-pass processing)."""
        pass
    
    def get_priority(self) -> int:
        """Get provider priority (lower = higher priority)."""
        return self.config.priority
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information for logging."""
        return {
            "name": self.config.name,
            "type": self.config.provider_type.value,
            "model": self.config.model_name,
            "enabled": self.config.enabled,
            "priority": self.config.priority
        }


class ClaudeProvider(AIProvider):
    """Claude AI provider using Anthropic's API."""
    
    def _initialize(self) -> None:
        """Initialize Claude provider."""
        if not self.config.api_key:
            raise ValueError("Claude provider requires API key")
        
        self.api_url = self.config.api_url or "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Claude 3.5 Sonnet has a large context window (200k tokens)
        self.max_context_tokens = 200000
        
    def is_available(self) -> bool:
        """Check if Claude API is available."""
        try:
            # Simple health check
            test_payload = {
                "model": self.config.model_name,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            
            return response.status_code in [200, 429]  # 429 = rate limited but available
            
        except Exception as e:
            self.logger.warning(f"Claude availability check failed: {e}")
            return False
    
    def supports_full_transcript(self, context: ProcessingContext) -> bool:
        """Claude 3.5 Sonnet can handle very large transcripts."""
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = context.file_size // 4
        
        # Reserve space for prompt and response
        max_input_tokens = self.max_context_tokens - 4000  # Reserve 4k for prompt + response
        
        return estimated_tokens < max_input_tokens
    
    def generate_summary(self, prompt: str, transcript: str, context: ProcessingContext) -> AIResponse:
        """Generate summary using Claude."""
        start_time = time.time()
        
        try:
            # Construct the full prompt
            full_prompt = f"{prompt}\n\n**TRANSCRIPT CONTENT:**\n{transcript}"
            
            payload = {
                "model": self.config.model_name,
                "max_tokens": self.config.max_tokens or 4000,
                "temperature": self.config.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                
                # Log success metrics
                log_performance_metrics(
                    "claude_summary",
                    processing_time,
                    success=True,
                    model=self.config.model_name,
                    tokens_used=result.get("usage", {}).get("input_tokens", 0)
                )
                
                return AIResponse(
                    success=True,
                    content=content,
                    provider_used=self.config.name,
                    model_used=self.config.model_name,
                    processing_time=processing_time,
                    tokens_used=result.get("usage", {}).get("input_tokens", 0),
                    metadata={"response_id": result.get("id")}
                )
            
            else:
                error_msg = f"Claude API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                log_performance_metrics("claude_summary", processing_time, success=False)
                
                return AIResponse(
                    success=False,
                    error=error_msg,
                    provider_used=self.config.name,
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Claude processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            log_performance_metrics("claude_summary", processing_time, success=False)
            
            return AIResponse(
                success=False,
                error=error_msg,
                provider_used=self.config.name,
                processing_time=processing_time
            )
    
    def extract_entities(self, transcript: str, context: ProcessingContext) -> AIResponse:
        """Extract entities using Claude (for future use)."""
        start_time = time.time()
        
        try:
            # Entity extraction prompt
            entity_prompt = """Extract key entities from this meeting transcript. Focus on:
            1. Technical terms and system names
            2. People's names and roles
            3. Business concepts and decisions
            4. Action items and deadlines
            5. Important dates and numbers
            
            Return as a JSON object with categorized entities."""
            
            full_prompt = f"{entity_prompt}\n\nTranscript:\n{transcript}"
            
            payload = {
                "model": self.config.model_name,
                "max_tokens": 1000,
                "temperature": 0.0,  # More deterministic for entity extraction
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                
                return AIResponse(
                    success=True,
                    content=content,
                    provider_used=self.config.name,
                    model_used=self.config.model_name,
                    processing_time=processing_time
                )
            else:
                return AIResponse(
                    success=False,
                    error=f"Entity extraction failed: {response.status_code}",
                    provider_used=self.config.name,
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return AIResponse(
                success=False,
                error=f"Entity extraction error: {str(e)}",
                provider_used=self.config.name,
                processing_time=processing_time
            )


class OllamaProvider(AIProvider):
    """Enhanced Ollama provider with two-pass processing."""
    
    def _initialize(self) -> None:
        """Initialize Ollama provider."""
        self.api_url = self.config.api_url or "http://localhost:11434"
        self.generate_url = f"{self.api_url}/api/generate"
        
        # Ollama models have smaller context windows
        self.max_context_tokens = 8192  # Typical for Llama models
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama availability check failed: {e}")
            return False
    
    def supports_full_transcript(self, context: ProcessingContext) -> bool:
        """Ollama typically needs chunking for large transcripts."""
        # Conservative estimate: 1 token ≈ 4 characters
        estimated_tokens = context.file_size // 4
        
        # Reserve space for prompt and response
        max_input_tokens = self.max_context_tokens - 2000
        
        return estimated_tokens < max_input_tokens
    
    def generate_summary(self, prompt: str, transcript: str, context: ProcessingContext) -> AIResponse:
        """Generate summary using Ollama with enhanced processing."""
        start_time = time.time()
        
        try:
            # Use persona-based prompt for better results
            enhanced_prompt = self._create_persona_prompt(prompt, context)
            full_prompt = f"{enhanced_prompt}\n\n**TRANSCRIPT:**\n{transcript}"
            
            payload = {
                "model": self.config.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.config.timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                
                log_performance_metrics(
                    "ollama_summary",
                    processing_time,
                    success=True,
                    model=self.config.model_name
                )
                
                return AIResponse(
                    success=True,
                    content=content,
                    provider_used=self.config.name,
                    model_used=self.config.model_name,
                    processing_time=processing_time,
                    metadata={"eval_count": result.get("eval_count", 0)}
                )
            
            else:
                error_msg = f"Ollama error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                log_performance_metrics("ollama_summary", processing_time, success=False)
                
                return AIResponse(
                    success=False,
                    error=error_msg,
                    provider_used=self.config.name,
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Ollama processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            log_performance_metrics("ollama_summary", processing_time, success=False)
            
            return AIResponse(
                success=False,
                error=error_msg,
                provider_used=self.config.name,
                processing_time=processing_time
            )
    
    def extract_entities(self, transcript: str, context: ProcessingContext) -> AIResponse:
        """Extract entities using focused Ollama prompt."""
        start_time = time.time()
        
        try:
            # Focused entity extraction prompt
            entity_prompt = f"""You are a Technical Information Extractor. Your ONLY job is to scan this meeting transcript and extract key terms.

EXTRACT THESE ITEMS ONLY:
1. **People**: Names of speakers and who they are
2. **Systems**: Technical systems, APIs, services, tools mentioned
3. **Decisions**: Clear technical or business choices made
4. **Actions**: Specific tasks assigned to people
5. **Technical Terms**: Architecture patterns, technologies, frameworks

FORMAT: Simple bullet points, no explanations.

Meeting: {context.meeting_title}
Participants: {', '.join(context.participants)}

Transcript: {transcript}

EXTRACT KEY TERMS NOW:"""

            payload = {
                "model": self.config.model_name,
                "prompt": entity_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Deterministic
                    "top_k": 10,
                    "top_p": 0.5
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=30  # Shorter timeout for entity extraction
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                
                return AIResponse(
                    success=True,
                    content=content,
                    provider_used=self.config.name,
                    model_used=self.config.model_name,
                    processing_time=processing_time
                )
            else:
                return AIResponse(
                    success=False,
                    error=f"Entity extraction failed: {response.status_code}",
                    provider_used=self.config.name,
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return AIResponse(
                success=False,
                error=f"Entity extraction error: {str(e)}",
                provider_used=self.config.name,
                processing_time=processing_time
            )
    
    def _create_persona_prompt(self, base_prompt: str, context: ProcessingContext) -> str:
        """Create a persona-based prompt for better Ollama performance."""
        persona = f"""You are a Senior Engineering Manager with 15+ years of experience at top tech companies. 

You excel at:
- Understanding technical architecture discussions
- Extracting business context from engineering conversations  
- Identifying specific technical decisions and trade-offs
- Recognizing action items and ownership

You are analyzing a {context.meeting_type} meeting titled "{context.meeting_title}" with {len(context.participants)} participants.

CRITICAL: Focus ONLY on concrete technical and business details mentioned in the transcript. Do NOT add generic commentary or assumptions."""

        return f"{persona}\n\n{base_prompt}"


class AIProviderManager:
    """Manages multiple AI providers with fallback logic."""
    
    def __init__(self):
        self.logger = get_logger("ai_provider_manager")
        self.providers: List[AIProvider] = []
        self._load_providers()
    
    def _load_providers(self) -> None:
        """Load and initialize AI providers from configuration."""
        config = get_config()
        
        # Load provider configurations
        provider_configs = []
        
        # Try to load ai_providers configuration from YAML
        try:
            # Get raw config for ai_providers section
            from pathlib import Path
            import yaml
            
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "settings.yaml"
            
            with open(config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            ai_providers = raw_config.get('ai_providers', {})
            
            # Check for Claude configuration
            claude_config = ai_providers.get('claude', {})
            if claude_config.get('enabled', False):
                api_key = claude_config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    provider_configs.append(AIProviderConfig(
                        name="claude",
                        provider_type=AIProviderType.CLAUDE,
                        model_name=claude_config.get('model_name', 'claude-3-5-sonnet-20241022'),
                        api_key=api_key,
                        max_tokens=claude_config.get('max_tokens', 4000),
                        temperature=claude_config.get('temperature', 0.1),
                        timeout=claude_config.get('timeout', 120),
                        priority=claude_config.get('priority', 1)
                    ))
        
        except Exception as e:
            self.logger.warning(f"Could not load ai_providers config: {e}")
        
        # Always add Ollama as fallback
        provider_configs.append(AIProviderConfig(
            name="ollama",
            provider_type=AIProviderType.OLLAMA,
            model_name=config.processing.model_name,
            api_url=config.processing.ollama_url,
            temperature=0.1,
            timeout=config.processing.request_timeout,
            priority=2  # Lower priority than Claude
        ))
        
        # Initialize providers
        for provider_config in provider_configs:
            try:
                if provider_config.provider_type == AIProviderType.CLAUDE:
                    provider = ClaudeProvider(provider_config)
                elif provider_config.provider_type == AIProviderType.OLLAMA:
                    provider = OllamaProvider(provider_config)
                else:
                    continue
                
                self.providers.append(provider)
                self.logger.info(f"Initialized AI provider: {provider_config.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize provider {provider_config.name}: {e}")
        
        # Sort providers by priority
        self.providers.sort(key=lambda p: p.get_priority())
        
        if not self.providers:
            raise RuntimeError("No AI providers available")
        
        self.logger.info(f"Loaded {len(self.providers)} AI providers")
    
    def get_best_provider(self, context: ProcessingContext) -> Optional[AIProvider]:
        """Get the best available provider for the given context with cost optimization."""
        
        # Cost-optimized routing based on meeting type and complexity
        meeting_type = context.meeting_type.lower()
        
        # Use local Ollama for simple/routine meetings to save costs
        local_suitable_meetings = ['standup', 'daily', 'scrum', 'all_hands', 'general']
        
        # Use Claude only for complex/strategic meetings
        cloud_priority_meetings = ['strategy', 'technical', 'architecture', 'one_on_one', 'alignment']
        
        # If it's a simple meeting type, prefer local processing
        if any(simple_type in meeting_type for simple_type in local_suitable_meetings):
            self.logger.info("🏠 Using local processing for routine meeting (cost optimization)")
            for provider in reversed(self.providers):  # Start with lowest priority (Ollama)
                if (provider.config.provider_type == AIProviderType.OLLAMA and 
                    provider.config.enabled and provider.is_available()):
                    self.logger.info(f"Selected provider: {provider.config.name} (cost-optimized)")
                    return provider
        
        # For complex meetings or if local isn't available, use standard priority order
        for provider in self.providers:
            if not provider.config.enabled:
                continue
                
            if not provider.is_available():
                self.logger.warning(f"Provider {provider.config.name} is not available")
                continue
            
            self.logger.info(f"Selected provider: {provider.config.name}")
            return provider
        
        self.logger.error("No AI providers available")
        return None
    
    def process_with_fallback(self, prompt: str, transcript: str, context: ProcessingContext) -> AIResponse:
        """Process transcript with automatic fallback between providers."""
        for provider in self.providers:
            if not provider.config.enabled or not provider.is_available():
                continue
            
            self.logger.info(f"Attempting processing with {provider.config.name}")
            
            # For local models, use two-pass processing if transcript is large
            if (provider.config.provider_type == AIProviderType.OLLAMA and 
                not provider.supports_full_transcript(context)):
                
                return self._two_pass_processing(provider, prompt, transcript, context)
            
            # For cloud models or small transcripts, process directly
            response = provider.generate_summary(prompt, transcript, context)
            
            if response.success:
                self.logger.info(f"Successfully processed with {provider.config.name}")
                return response
            
            self.logger.warning(f"Provider {provider.config.name} failed: {response.error}")
        
        # All providers failed
        return AIResponse(
            success=False,
            error="All AI providers failed",
            provider_used="none"
        )
    
    def _two_pass_processing(self, provider: AIProvider, prompt: str, transcript: str, context: ProcessingContext) -> AIResponse:
        """Implement two-pass processing for local models."""
        self.logger.info("Using two-pass processing for large transcript")
        
        # Pass 1: Extract entities
        entity_response = provider.extract_entities(transcript, context)
        
        if not entity_response.success:
            self.logger.warning("Entity extraction failed, falling back to chunked processing")
            # TODO: Implement chunked processing fallback
            return AIResponse(
                success=False,
                error="Two-pass processing failed",
                provider_used=provider.config.name
            )
        
        # Pass 2: Generate summary with entity context
        enhanced_prompt = f"""{prompt}

**KEY ENTITIES EXTRACTED FROM TRANSCRIPT:**
{entity_response.content}

**INSTRUCTION:** Use the above entities as a reference to ensure your summary captures the most important technical and business details mentioned in the meeting."""
        
        summary_response = provider.generate_summary(enhanced_prompt, transcript, context)
        
        if summary_response.success:
            # Combine metadata from both passes
            summary_response.metadata = summary_response.metadata or {}
            summary_response.metadata.update({
                "processing_type": "two_pass",
                "entity_extraction_time": entity_response.processing_time,
                "entities_extracted": entity_response.content[:200] + "..." if len(entity_response.content) > 200 else entity_response.content
            })
        
        return summary_response
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        
        for provider in self.providers:
            status[provider.config.name] = {
                "available": provider.is_available(),
                "enabled": provider.config.enabled,
                "priority": provider.config.priority,
                "model": provider.config.model_name,
                "type": provider.config.provider_type.value
            }
        
        return status 