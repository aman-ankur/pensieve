"""
AI processing module for Pensieve.
Handles communication with Ollama and generates meeting summaries.
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..utils.config import get_config
from ..utils.logger import get_logger, log_performance_metrics
from .context_aware_chunker import ContextAwareChunker, ContextualChunk


@dataclass
class MeetingMetadata:
    """Metadata extracted from meeting transcript."""
    title: str
    date: str
    duration: str
    participants: List[str]
    meeting_type: str
    file_path: str
    file_size: int


@dataclass
class ProcessingResult:
    """Result of transcript processing."""
    success: bool
    summary: Optional[str] = None
    metadata: Optional[MeetingMetadata] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    model_used: str = ""
    chunks_processed: int = 0


class TranscriptParser:
    """Parses Zoom transcript files and extracts metadata."""
    
    def __init__(self):
        self.logger = get_logger("transcript_parser")
        self.config = get_config()
    
    def parse_transcript(self, file_path: Path) -> tuple[str, MeetingMetadata]:
        """
        Parse a Zoom transcript file and extract content + metadata.
        
        Args:
            file_path: Path to the transcript file.
            
        Returns:
            Tuple of (transcript_content, metadata).
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is invalid.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        start_time = time.time()
        
        try:
            # Read transcript content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError("Transcript file is empty")
            
            # Extract metadata from folder name and content
            metadata = self._extract_metadata(file_path, content)
            
            # Clean and format content
            cleaned_content = self._clean_transcript_content(content)
            
            processing_time = time.time() - start_time
            log_performance_metrics(
                "transcript_parsing", 
                processing_time, 
                success=True,
                file_size=len(content),
                participants=len(metadata.participants)
            )
            
            return cleaned_content, metadata
            
        except Exception as e:
            processing_time = time.time() - start_time
            log_performance_metrics("transcript_parsing", processing_time, success=False)
            raise
    
    def _extract_metadata(self, file_path: Path, content: str) -> MeetingMetadata:
        """Extract meeting metadata from file path and content."""
        # Parse folder name: "YYYY-MM-DD HH.MM.SS Meeting Title"
        folder_name = file_path.parent.name
        parts = folder_name.split(' ', 2)
        
        if len(parts) >= 3:
            date_str = parts[0]
            time_str = parts[1]
            title = parts[2] if len(parts) > 2 else "Untitled Meeting"
        else:
            date_str = "Unknown"
            time_str = "Unknown"
            title = folder_name
        
        # Extract participants from transcript
        participants = self._extract_participants(content)
        
        # Determine meeting type
        meeting_type = self._classify_meeting_type(title, participants)
        
        # Calculate duration (rough estimate from content)
        duration = self._estimate_duration(content)
        
        return MeetingMetadata(
            title=title,
            date=f"{date_str} {time_str}".replace('.', ':'),
            duration=duration,
            participants=participants,
            meeting_type=meeting_type,
            file_path=str(file_path),
            file_size=file_path.stat().st_size
        )
    
    def _extract_participants(self, content: str) -> List[str]:
        """Extract participant names from transcript content."""
        participants = set()
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for speaker pattern: "[Speaker Name] HH:MM:SS"
            if line.count(' ') >= 1:
                # Find the timestamp pattern at the end
                parts = line.split(' ')
                
                # Check if last part looks like a timestamp
                last_part = parts[-1]
                if ':' in last_part and len(last_part) <= 8:
                    # Extract speaker name (everything except the timestamp)
                    speaker = ' '.join(parts[:-1])
                    if speaker and not speaker.startswith('[') and len(speaker) < 50:
                        participants.add(speaker)
        
        return sorted(list(participants))
    
    def _classify_meeting_type(self, title: str, participants: List[str]) -> str:
        """Classify meeting type based on title and participants."""
        title_lower = title.lower()
        
        # Check configured meeting types
        for meeting_type, config in self.config.meeting_types.items():
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return meeting_type.replace('_', ' ').title()
        
        # Basic classification based on participant count
        if len(participants) <= 2:
            return "One-on-One"
        elif len(participants) <= 5:
            return "Small Team Meeting"
        else:
            return "Group Meeting"
    
    def _estimate_duration(self, content: str) -> str:
        """Estimate meeting duration from transcript timestamps."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if len(lines) < 2:
            return "Unknown"
        
        # Extract first and last timestamps
        first_timestamp = None
        last_timestamp = None
        
        for line in lines:
            parts = line.split(' ')
            if len(parts) >= 2:
                potential_time = parts[-1]
                if ':' in potential_time and len(potential_time) <= 8:
                    try:
                        # Parse time format HH:MM:SS or MM:SS
                        time_parts = potential_time.split(':')
                        if len(time_parts) >= 2:
                            if first_timestamp is None:
                                first_timestamp = potential_time
                            last_timestamp = potential_time
                    except:
                        continue
        
        if first_timestamp and last_timestamp and first_timestamp != last_timestamp:
            try:
                # Simple duration calculation (rough estimate)
                return f"~{self._calculate_time_diff(first_timestamp, last_timestamp)}"
            except:
                pass
        
        # Fallback: estimate based on content length
        word_count = len(content.split())
        estimated_minutes = max(5, word_count // 150)  # ~150 words per minute
        return f"~{estimated_minutes}m"
    
    def _calculate_time_diff(self, start_time: str, end_time: str) -> str:
        """Calculate difference between two timestamp strings."""
        try:
            # Parse timestamps (handle both HH:MM:SS and MM:SS formats)
            def parse_time(time_str):
                parts = time_str.split(':')
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
                return 0
            
            start_seconds = parse_time(start_time)
            end_seconds = parse_time(end_time)
            
            diff_seconds = end_seconds - start_seconds
            if diff_seconds < 0:
                diff_seconds += 24 * 3600  # Handle day boundary
            
            if diff_seconds < 60:
                return f"{diff_seconds}s"
            elif diff_seconds < 3600:
                return f"{diff_seconds // 60}m"
            else:
                hours = diff_seconds // 3600
                minutes = (diff_seconds % 3600) // 60
                return f"{hours}h{minutes}m"
                
        except:
            return "Unknown"
    
    def _clean_transcript_content(self, content: str) -> str:
        """Clean and format transcript content for AI processing."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip very short lines that might be artifacts
            if len(line) < 3:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)


class TranscriptChunker:
    """Handles chunking of large transcripts for processing."""
    
    def __init__(self, max_chunk_size: int = 2000):
        """
        Initialize chunker.
        
        Args:
            max_chunk_size: Maximum size of each chunk in characters.
        """
        self.max_chunk_size = max_chunk_size
        self.logger = get_logger("chunker")
    
    def should_chunk(self, content: str) -> bool:
        """Check if content should be chunked."""
        return len(content) > self.max_chunk_size
    
    def create_chunks(self, content: str, metadata: MeetingMetadata) -> List[Dict[str, str]]:
        """
        Create chunks from transcript content.
        
        Args:
            content: Transcript content to chunk.
            metadata: Meeting metadata.
            
        Returns:
            List of chunks with metadata.
        """
        if not self.should_chunk(content):
            return [{
                "content": content,
                "chunk_info": "Complete transcript (single chunk)",
                "chunk_number": 1,
                "total_chunks": 1
            }]
        
        # Split by speaker segments first
        segments = self._split_by_speakers(content)
        
        # Group segments into chunks
        chunks = self._group_segments_into_chunks(segments)
        
        # Add metadata to chunks
        result_chunks = []
        for i, chunk_content in enumerate(chunks, 1):
            result_chunks.append({
                "content": chunk_content,
                "chunk_info": f"Chunk {i}/{len(chunks)}",
                "chunk_number": i,
                "total_chunks": len(chunks)
            })
        
        self.logger.info(f"📄 Split large transcript into {len(chunks)} chunks (~{self.max_chunk_size} chars each)")
        return result_chunks
    
    def _split_by_speakers(self, content: str) -> List[str]:
        """Split content by speaker segments."""
        lines = content.split('\n')
        segments = []
        current_segment = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new speaker segment
            parts = line.split(' ')
            if len(parts) >= 2 and ':' in parts[-1] and len(parts[-1]) <= 8:
                # This looks like a speaker line
                if current_segment:
                    segments.append('\n'.join(current_segment))
                    current_segment = []
                current_segment.append(line)
            else:
                # This is content from the current speaker
                if current_segment:
                    current_segment.append(line)
        
        # Add the last segment
        if current_segment:
            segments.append('\n'.join(current_segment))
        
        return segments
    
    def _group_segments_into_chunks(self, segments: List[str]) -> List[str]:
        """Group segments into appropriately sized chunks."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for segment in segments:
            segment_size = len(segment)
            
            # If adding this segment would exceed max size, start a new chunk
            if current_size + segment_size > self.max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(segment)
            current_size += segment_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks


class OllamaClient:
    """Client for communicating with Ollama API."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("ollama_client")
        self.base_url = self.config.processing.ollama_url
        
    def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_summary(self, prompt: str, model: str = None) -> str:
        """
        Generate summary using Ollama.
        
        Args:
            prompt: The formatted prompt to send to the model.
            model: Model name to use (uses config default if None).
            
        Returns:
            Generated summary text.
            
        Raises:
            requests.RequestException: If API call fails.
            ValueError: If response is invalid.
        """
        model = model or self.config.processing.model_name
        start_time = time.time()
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 4096,  # Reduced context window for faster processing
                }
            }
            
            self.logger.debug(f"Sending request to Ollama with model: {model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.processing.request_timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "response" not in result:
                raise ValueError("Invalid response format from Ollama")
            
            summary = result["response"].strip()
            
            processing_time = time.time() - start_time
            log_performance_metrics(
                "ollama_generation",
                processing_time,
                success=True,
                model=model,
                prompt_length=len(prompt),
                response_length=len(summary)
            )
            
            return summary
            
        except Exception as e:
            processing_time = time.time() - start_time
            log_performance_metrics("ollama_generation", processing_time, success=False)
            raise


class AIProcessor:
    """Main AI processor that orchestrates transcript processing."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("ai_processor")
        self.parser = TranscriptParser()
        self.ollama = OllamaClient()
        
        # Configure chunking based on settings
        if hasattr(self.config.processing, 'chunking') and self.config.processing.chunking:
            chunk_size = self.config.processing.chunking.get('max_chunk_size', 2000)
            overlap_size = self.config.processing.chunking.get('overlap_size', 300)
        else:
            chunk_size = 2000
            overlap_size = 300
        
        # Use context-aware chunker for better quality
        self.context_chunker = ContextAwareChunker(max_chunk_size=chunk_size, overlap_size=overlap_size)
        # Keep old chunker for fallback
        self.chunker = TranscriptChunker(max_chunk_size=chunk_size)
        
        # Load prompt templates
        self.full_template = self._load_prompt_template()
        self.chunk_template = self._get_chunk_template()
        self.synthesis_template = self._get_synthesis_template()
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        try:
            template_path = Path(self.config.output.template_file)
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"Template file not found: {template_path}")
                return self._get_default_template()
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Get a basic default template if file loading fails."""
        return """
Please analyze this meeting transcript and create a structured summary.

Meeting: {meeting_title}
Date: {meeting_date}
Participants: {participants}

Transcript:
{transcript_content}

Please provide:
1. Key Discussion Points (3-5 bullets)
2. Action Items (with person and deadline)
3. Decisions Made
4. Next Steps
"""
    
    def _get_chunk_template(self) -> str:
        """Get template for processing individual chunks."""
        try:
            template_path = Path("config/prompts/chunk_template.txt")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"Chunk template file not found: {template_path}")
                return self._get_default_chunk_template()
        except Exception as e:
            self.logger.error(f"Error loading chunk template: {e}")
            return self._get_default_chunk_template()
    
    def _get_default_chunk_template(self) -> str:
        """Get default chunk template if file loading fails."""
        return """
Analyze this meeting section for work-related content only. Skip personal chat.

{chunk_info}: {meeting_title}

{transcript_content}

Extract from this section:
• Technical/business topics discussed
• Specific decisions or choices made  
• Action items with person responsible
• Technical details (systems, APIs, architecture)
• Open questions or concerns raised

Focus on substance, skip casual conversation.
"""
    
    def _get_synthesis_template(self) -> str:
        """Get template for synthesizing chunk summaries."""
        try:
            template_path = Path("config/prompts/synthesis_template.txt")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"Synthesis template file not found: {template_path}")
                return self._get_default_synthesis_template()
        except Exception as e:
            self.logger.error(f"Error loading synthesis template: {e}")
            return self._get_default_synthesis_template()
    
    def _get_default_synthesis_template(self) -> str:
        """Get default synthesis template if file loading fails."""
        return """
Create a professional meeting summary from these section analyses. Focus on business/technical content.

Meeting: {meeting_title}
Date: {meeting_date}
Participants: {participants}
Type: {meeting_type}

Section summaries:
{chunk_summaries}

Create a comprehensive summary:

## 🎯 Meeting Purpose & Context
[What business/technical challenge was being addressed?]

## 📋 Key Discussion Points
[4-6 substantive topics with technical details - not generic statements]
- **[Topic]**: [Specific details, options considered, technical context]

## ✅ Action Items
[Concrete tasks with clear ownership]
- [ ] **@Person** - Specific task - **Due: Timeline** - *Priority: Level*

## 🎯 Decisions Made
[Clear decisions with reasoning]

## 🔄 Next Steps & Follow-ups
[Planned activities and future meetings]

## 🤔 Open Questions & Risks
[Unresolved issues needing attention]

## 📝 Technical Notes
[Important technical details, systems mentioned, architectural decisions]

Focus on actionable, specific content. Exclude casual conversation.
"""
    
    def process_transcript(self, file_path: Path) -> ProcessingResult:
        """
        Process a transcript file and generate summary.
        
        Args:
            file_path: Path to the transcript file.
            
        Returns:
            ProcessingResult with summary and metadata.
        """
        start_time = time.time()
        
        try:
            # Check if Ollama is available
            if not self.ollama.is_available():
                return ProcessingResult(
                    success=False,
                    error="Ollama is not available. Please ensure it's running.",
                    processing_time=time.time() - start_time
                )
            
            # Parse transcript
            self.logger.info(f"📖 Parsing transcript: {file_path.parent.name}")
            transcript_content, metadata = self.parser.parse_transcript(file_path)
            
            # Check if we need to chunk the content
            if self.context_chunker.should_chunk(transcript_content):
                self.logger.info(f"📄 Large transcript detected, using context-aware chunked processing")
                summary = self._process_contextual_chunks(transcript_content, metadata)
                chunks_processed = len(self.context_chunker.create_contextual_chunks(transcript_content, metadata))
            else:
                self.logger.info(f"🤖 Generating summary with {self.config.processing.model_name}")
                prompt = self._format_prompt(transcript_content, metadata)
                summary = self.ollama.generate_summary(prompt)
                chunks_processed = 1
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"✅ Summary generated successfully in {processing_time:.1f}s")
            
            return ProcessingResult(
                success=True,
                summary=summary,
                metadata=metadata,
                processing_time=processing_time,
                model_used=self.config.processing.model_name,
                chunks_processed=chunks_processed
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ProcessingResult(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def _process_contextual_chunks(self, transcript_content: str, metadata: MeetingMetadata) -> str:
        """Process a large transcript using context-aware chunking."""
        # Create contextual chunks
        contextual_chunks = self.context_chunker.create_contextual_chunks(transcript_content, metadata)
        
        # Use fast model for chunk processing
        fast_model = getattr(self.config.processing, 'chunk_model', 'llama3.2:1b')
        synthesis_model = getattr(self.config.processing, 'synthesis_model', 'llama3.1:8b')
        
        self.logger.info(f"🚀 Using {fast_model} for chunks, {synthesis_model} for synthesis")
        
        # Process each contextual chunk
        chunk_summaries = []
        for chunk in contextual_chunks:
            # Format prompt with context information
            prompt = self.chunk_template.format(
                previous_context=chunk.previous_context or "This is the first section of the meeting.",
                overlap_content=chunk.overlap_content or "No overlap content.",
                chunk_info=chunk.chunk_info,
                transcript_content=chunk.content
            )
            
            self.logger.info(f"⚡ Processing {chunk.chunk_info} with {fast_model}")
            chunk_summary = self.ollama.generate_summary(prompt, model=fast_model)
            chunk_summaries.append(f"### {chunk.chunk_info}\n{chunk_summary}")
        
        # Synthesize final summary with better model
        self.logger.info(f"🔗 Synthesizing final summary with {synthesis_model}")
        synthesis_prompt = self.synthesis_template.format(
            meeting_title=metadata.title,
            meeting_date=metadata.date,
            participants=", ".join(metadata.participants),
            meeting_type=metadata.meeting_type,
            chunk_summaries="\n\n".join(chunk_summaries)
        )
        
        final_summary = self.ollama.generate_summary(synthesis_prompt, model=synthesis_model)
        return final_summary

    def _process_chunked_transcript(self, transcript_content: str, metadata: MeetingMetadata) -> str:
        """Process a large transcript using chunking."""
        # Create chunks
        chunks = self.chunker.create_chunks(transcript_content, metadata)
        
        # Use fast model for chunk processing
        fast_model = getattr(self.config.processing, 'chunk_model', 'llama3.2:1b')
        synthesis_model = getattr(self.config.processing, 'synthesis_model', 'llama3.1:8b')
        
        self.logger.info(f"🚀 Using {fast_model} for chunks, {synthesis_model} for synthesis")
        
        # Process each chunk with fast model
        chunk_summaries = []
        for chunk in chunks:
            prompt = self.chunk_template.format(
                meeting_title=metadata.title,
                chunk_info=chunk["chunk_info"],
                transcript_content=chunk["content"]
            )
            
            self.logger.info(f"⚡ Processing {chunk['chunk_info']} with {fast_model}")
            chunk_summary = self.ollama.generate_summary(prompt, model=fast_model)
            chunk_summaries.append(f"### {chunk['chunk_info']}\n{chunk_summary}")
        
        # Synthesize final summary with better model
        self.logger.info(f"🔗 Synthesizing final summary with {synthesis_model}")
        synthesis_prompt = self.synthesis_template.format(
            meeting_title=metadata.title,
            meeting_date=metadata.date,
            participants=", ".join(metadata.participants),
            meeting_type=metadata.meeting_type,
            chunk_summaries="\n\n".join(chunk_summaries)
        )
        
        final_summary = self.ollama.generate_summary(synthesis_prompt, model=synthesis_model)
        return final_summary
    
    def _format_prompt(self, transcript_content: str, metadata: MeetingMetadata) -> str:
        """Format the prompt with transcript and metadata."""
        return self.full_template.format(
            meeting_title=metadata.title,
            meeting_date=metadata.date,
            meeting_duration=metadata.duration,
            participants=", ".join(metadata.participants),
            meeting_type=metadata.meeting_type,
            transcript_content=transcript_content
        ) 