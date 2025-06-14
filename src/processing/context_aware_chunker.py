"""
Context-aware chunking system for meeting transcripts.
Preserves relationships and context across chunks, similar to Cursor's approach.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..utils.logger import get_logger


@dataclass
class ChunkContext:
    """Context information for a chunk."""
    chunk_id: str
    topic_summary: str
    key_entities: List[str]  # People, systems, technical terms
    ongoing_discussions: List[str]  # Topics that continue from previous chunks
    decisions_made: List[str]  # Decisions reached in this chunk
    action_items: List[str]  # Action items from this chunk


@dataclass 
class ContextualChunk:
    """A chunk with preserved context."""
    content: str
    chunk_info: str
    chunk_number: int
    total_chunks: int
    context: ChunkContext
    previous_context: Optional[str] = None  # Summary of previous chunks
    overlap_content: Optional[str] = None   # Overlapping content from previous chunk


class ContextAwareChunker:
    """
    Advanced chunking system that preserves context and relationships.
    Uses techniques similar to Cursor's document processing.
    """
    
    def __init__(self, max_chunk_size: int = 2500, overlap_size: int = 300):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.logger = get_logger("context_chunker")
        
        # Patterns for identifying important content
        self.technical_patterns = [
            r'\b(API|service|module|architecture|system|database|integration)\b',
            r'\b(deploy|test|build|release|version)\b',
            r'\b(performance|scalability|security|reliability)\b'
        ]
        
        self.decision_patterns = [
            r'\b(decide|decision|choose|option|approach|solution)\b',
            r'\b(agree|consensus|conclusion|final)\b',
            r'\b(go with|pick|select|prefer)\b'
        ]
        
        self.action_patterns = [
            r'\b(will|should|need to|have to|must)\b',
            r'\b(action|task|todo|follow.?up)\b',
            r'\b(by|due|deadline|timeline)\b'
        ]
    
    def should_chunk(self, content: str) -> bool:
        """Determine if content needs chunking."""
        return len(content) > self.max_chunk_size
    
    def create_contextual_chunks(self, content: str, metadata: Any) -> List[ContextualChunk]:
        """
        Create chunks with preserved context and relationships.
        
        Args:
            content: Full transcript content
            metadata: Meeting metadata
            
        Returns:
            List of contextual chunks with preserved relationships
        """
        if not self.should_chunk(content):
            # Single chunk - no context preservation needed
            context = self._extract_chunk_context(content, 1, 1)
            return [ContextualChunk(
                content=content,
                chunk_info="Complete transcript (single chunk)",
                chunk_number=1,
                total_chunks=1,
                context=context
            )]
        
        self.logger.info(f"🧠 Creating context-aware chunks for large transcript")
        
        # Step 1: Identify semantic boundaries (topics, speakers, decisions)
        semantic_segments = self._identify_semantic_segments(content)
        
        # Step 2: Group segments into chunks while preserving context
        raw_chunks = self._group_segments_with_context(semantic_segments)
        
        # Step 3: Add overlapping content and context summaries
        contextual_chunks = self._add_context_preservation(raw_chunks, metadata)
        
        self.logger.info(f"📄 Created {len(contextual_chunks)} context-aware chunks")
        return contextual_chunks
    
    def _identify_semantic_segments(self, content: str) -> List[Dict[str, Any]]:
        """
        Identify semantic segments in the transcript.
        Similar to how Cursor identifies logical sections in code.
        """
        lines = content.split('\n')
        segments = []
        current_segment = []
        current_topic = None
        current_speaker = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect speaker changes
            speaker = self._extract_speaker(line)
            if speaker and speaker != current_speaker:
                # Speaker change - potential segment boundary
                if current_segment:
                    segments.append({
                        'content': '\n'.join(current_segment),
                        'speaker': current_speaker,
                        'topic': current_topic,
                        'line_start': line_num - len(current_segment),
                        'line_end': line_num - 1,
                        'type': 'speaker_segment'
                    })
                
                current_segment = [line]
                current_speaker = speaker
                current_topic = self._detect_topic_change(line, current_topic)
            else:
                current_segment.append(line)
                
                # Check for topic changes within speaker
                new_topic = self._detect_topic_change(line, current_topic)
                if new_topic != current_topic:
                    current_topic = new_topic
        
        # Add final segment
        if current_segment:
            segments.append({
                'content': '\n'.join(current_segment),
                'speaker': current_speaker,
                'topic': current_topic,
                'line_start': len(lines) - len(current_segment),
                'line_end': len(lines) - 1,
                'type': 'speaker_segment'
            })
        
        return segments
    
    def _extract_speaker(self, line: str) -> Optional[str]:
        """Extract speaker name from a line."""
        parts = line.split(' ')
        if len(parts) >= 2 and ':' in parts[-1] and len(parts[-1]) <= 8:
            # This looks like a speaker line: "Speaker Name HH:MM:SS"
            return ' '.join(parts[:-1])
        return None
    
    def _detect_topic_change(self, line: str, current_topic: Optional[str]) -> Optional[str]:
        """
        Detect topic changes using keyword patterns.
        Similar to how Cursor detects function/class boundaries.
        """
        line_lower = line.lower()
        
        # Technical topics
        for pattern in self.technical_patterns:
            if re.search(pattern, line_lower):
                if 'architecture' in line_lower or 'system' in line_lower:
                    return 'technical_architecture'
                elif 'api' in line_lower or 'service' in line_lower:
                    return 'api_service'
                elif 'deploy' in line_lower or 'test' in line_lower:
                    return 'deployment_testing'
        
        # Decision topics
        for pattern in self.decision_patterns:
            if re.search(pattern, line_lower):
                return 'decision_making'
        
        # Action/planning topics
        for pattern in self.action_patterns:
            if re.search(pattern, line_lower):
                return 'action_planning'
        
        return current_topic
    
    def _group_segments_with_context(self, segments: List[Dict[str, Any]]) -> List[str]:
        """
        Group segments into chunks while preserving semantic boundaries.
        """
        chunks = []
        current_chunk_segments = []
        current_size = 0
        
        for segment in segments:
            segment_size = len(segment['content'])
            
            # Check if adding this segment would exceed size limit
            if current_size + segment_size > self.max_chunk_size and current_chunk_segments:
                # Create chunk from current segments
                chunk_content = '\n\n'.join([s['content'] for s in current_chunk_segments])
                chunks.append(chunk_content)
                
                # Start new chunk with overlap from previous
                if self.overlap_size > 0:
                    # Include last segment from previous chunk for context
                    current_chunk_segments = [current_chunk_segments[-1], segment]
                    current_size = len(current_chunk_segments[-2]['content']) + segment_size
                else:
                    current_chunk_segments = [segment]
                    current_size = segment_size
            else:
                current_chunk_segments.append(segment)
                current_size += segment_size
        
        # Add final chunk
        if current_chunk_segments:
            chunk_content = '\n\n'.join([s['content'] for s in current_chunk_segments])
            chunks.append(chunk_content)
        
        return chunks
    
    def _add_context_preservation(self, raw_chunks: List[str], metadata: Any) -> List[ContextualChunk]:
        """
        Add context preservation to chunks.
        Similar to how Cursor maintains context across file sections.
        """
        contextual_chunks = []
        previous_context_summary = None
        
        for i, chunk_content in enumerate(raw_chunks):
            chunk_number = i + 1
            total_chunks = len(raw_chunks)
            
            # Extract context for this chunk
            context = self._extract_chunk_context(chunk_content, chunk_number, total_chunks)
            
            # Add overlap content if not first chunk
            overlap_content = None
            if i > 0 and self.overlap_size > 0:
                # Get last part of previous chunk for context
                prev_chunk = raw_chunks[i-1]
                overlap_content = prev_chunk[-self.overlap_size:] if len(prev_chunk) > self.overlap_size else prev_chunk
            
            contextual_chunk = ContextualChunk(
                content=chunk_content,
                chunk_info=f"Chunk {chunk_number}/{total_chunks} - Topic: {context.topic_summary}",
                chunk_number=chunk_number,
                total_chunks=total_chunks,
                context=context,
                previous_context=previous_context_summary,
                overlap_content=overlap_content
            )
            
            contextual_chunks.append(contextual_chunk)
            
            # Update context summary for next chunk
            previous_context_summary = self._create_context_summary(context)
        
        return contextual_chunks
    
    def _extract_chunk_context(self, content: str, chunk_num: int, total_chunks: int) -> ChunkContext:
        """Extract context information from a chunk."""
        
        # Extract entities (people, systems, technical terms)
        entities = self._extract_entities(content)
        
        # Identify ongoing discussions
        ongoing_discussions = self._identify_discussions(content)
        
        # Extract decisions made
        decisions = self._extract_decisions(content)
        
        # Extract action items
        actions = self._extract_actions(content)
        
        # Generate topic summary
        topic_summary = self._generate_topic_summary(content, entities, ongoing_discussions)
        
        return ChunkContext(
            chunk_id=f"chunk_{chunk_num}",
            topic_summary=topic_summary,
            key_entities=entities,
            ongoing_discussions=ongoing_discussions,
            decisions_made=decisions,
            action_items=actions
        )
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract key entities (people, systems, technical terms)."""
        entities = set()
        
        # Extract people names (speakers)
        lines = content.split('\n')
        for line in lines:
            speaker = self._extract_speaker(line)
            if speaker:
                entities.add(speaker)
        
        # Extract technical terms
        content_lower = content.lower()
        technical_terms = ['api', 'service', 'module', 'system', 'database', 'architecture', 
                          'deployment', 'testing', 'integration', 'performance', 'security']
        
        for term in technical_terms:
            if term in content_lower:
                entities.add(term)
        
        return list(entities)[:10]  # Limit to top 10 entities
    
    def _identify_discussions(self, content: str) -> List[str]:
        """Identify ongoing discussion topics."""
        discussions = []
        
        # Look for question-answer patterns
        if '?' in content:
            discussions.append("Q&A discussion")
        
        # Look for decision-making language
        decision_keywords = ['option', 'choice', 'decide', 'approach', 'solution']
        for keyword in decision_keywords:
            if keyword in content.lower():
                discussions.append(f"Decision about {keyword}")
                break
        
        return discussions
    
    def _extract_decisions(self, content: str) -> List[str]:
        """Extract decisions made in this chunk."""
        decisions = []
        
        # Look for decision language
        decision_phrases = [
            r'we (decided|agreed|concluded)',
            r'(decision|choice) is',
            r'going with',
            r'final (decision|choice)'
        ]
        
        for phrase in decision_phrases:
            matches = re.finditer(phrase, content.lower())
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 100)
                decision_context = content[start:end].strip()
                decisions.append(decision_context)
        
        return decisions[:3]  # Limit to top 3 decisions
    
    def _extract_actions(self, content: str) -> List[str]:
        """Extract action items from this chunk."""
        actions = []
        
        # Look for action language
        action_phrases = [
            r'(will|should|need to) \w+',
            r'action item',
            r'follow up',
            r'by (next week|tomorrow|friday)'
        ]
        
        for phrase in action_phrases:
            matches = re.finditer(phrase, content.lower())
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 80)
                action_context = content[start:end].strip()
                actions.append(action_context)
        
        return actions[:5]  # Limit to top 5 actions
    
    def _generate_topic_summary(self, content: str, entities: List[str], discussions: List[str]) -> str:
        """Generate a brief topic summary for this chunk."""
        
        # Use entities and discussions to create summary
        if entities and discussions:
            return f"{', '.join(entities[:2])} discussing {', '.join(discussions[:2])}"
        elif entities:
            return f"Discussion involving {', '.join(entities[:3])}"
        elif discussions:
            return f"Discussion about {', '.join(discussions[:2])}"
        else:
            return "General discussion"
    
    def _create_context_summary(self, context: ChunkContext) -> str:
        """Create a summary of context for the next chunk."""
        summary_parts = []
        
        if context.key_entities:
            summary_parts.append(f"Key people/systems: {', '.join(context.key_entities[:3])}")
        
        if context.decisions_made:
            summary_parts.append(f"Decisions: {len(context.decisions_made)} made")
        
        if context.action_items:
            summary_parts.append(f"Actions: {len(context.action_items)} identified")
        
        return "; ".join(summary_parts) if summary_parts else "General discussion context" 