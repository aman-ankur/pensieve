#!/usr/bin/env python3
"""
Transcript preprocessor to reduce token usage and costs.
Removes filler words, repetitive content, and non-essential parts.
"""

import re
from typing import List, Tuple

class TranscriptPreprocessor:
    """Optimizes transcripts to reduce token usage while preserving meaning."""
    
    def __init__(self):
        # Common filler words that add no value
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 'sort of', 
            'kind of', 'actually', 'basically', 'literally', 'honestly',
            'well', 'so', 'right', 'okay', 'alright', 'yeah', 'yes', 'no'
        }
        
        # Zoom-specific noise patterns
        self.zoom_patterns = [
            r'\d{2}:\d{2}:\d{2}',  # Timestamps
            r'You are now recording this meeting',
            r'Recording in progress',
            r'This meeting is being recorded',
            r'\[PARTICIPANT_\d+\]',  # Generic participant labels
            r'\(phone ringing\)',
            r'\(background noise\)',
            r'\(inaudible\)',
            r'\[pause\]',
            r'\[silence\]'
        ]
    
    def optimize_transcript(self, transcript: str) -> Tuple[str, dict]:
        """
        Optimize transcript to reduce tokens while preserving meaning.
        Returns optimized transcript and optimization stats.
        """
        original_length = len(transcript)
        original_words = len(transcript.split())
        
        # Step 1: Remove Zoom-specific noise
        cleaned = self._remove_zoom_noise(transcript)
        
        # Step 2: Remove excessive filler words (but keep some for natural flow)
        cleaned = self._reduce_filler_words(cleaned)
        
        # Step 3: Consolidate repetitive statements
        cleaned = self._consolidate_repetition(cleaned)
        
        # Step 4: Remove excessive whitespace and formatting
        cleaned = self._normalize_whitespace(cleaned)
        
        # Calculate savings
        optimized_length = len(cleaned)
        optimized_words = len(cleaned.split())
        
        stats = {
            'original_chars': original_length,
            'optimized_chars': optimized_length,
            'chars_saved': original_length - optimized_length,
            'chars_reduction_pct': ((original_length - optimized_length) / original_length) * 100,
            'original_words': original_words,
            'optimized_words': optimized_words,
            'words_saved': original_words - optimized_words,
            'words_reduction_pct': ((original_words - optimized_words) / original_words) * 100,
            'estimated_tokens_saved': (original_words - optimized_words) * 0.75  # ~0.75 tokens per word
        }
        
        return cleaned, stats
    
    def _remove_zoom_noise(self, text: str) -> str:
        """Remove Zoom-specific noise patterns."""
        for pattern in self.zoom_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _reduce_filler_words(self, text: str) -> str:
        """
        Reduce (but don't eliminate) filler words.
        Keep some for natural flow, remove excessive usage.
        """
        words = text.split()
        cleaned_words = []
        consecutive_fillers = 0
        
        for word in words:
            word_clean = word.lower().strip('.,!?')
            
            if word_clean in self.filler_words:
                consecutive_fillers += 1
                # Keep first filler in a sequence, skip excessive ones
                if consecutive_fillers <= 1:
                    cleaned_words.append(word)
            else:
                consecutive_fillers = 0
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    def _consolidate_repetition(self, text: str) -> str:
        """
        Identify and consolidate repetitive statements.
        Common in meetings where people repeat points.
        """
        sentences = re.split(r'[.!?]+', text)
        
        # Simple repetition detection - if same sentence appears multiple times
        seen_sentences = {}
        consolidated = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short fragments
                consolidated.append(sentence)
                continue
            
            # Normalize for comparison (lowercase, remove minor variations)
            normalized = re.sub(r'\s+', ' ', sentence.lower())
            
            if normalized in seen_sentences:
                seen_sentences[normalized] += 1
                # Skip if we've seen this exact point more than twice
                if seen_sentences[normalized] <= 2:
                    consolidated.append(sentence)
            else:
                seen_sentences[normalized] = 1
                consolidated.append(sentence)
        
        return '. '.join(filter(None, consolidated))
    
    def _normalize_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace and formatting."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Clean up around punctuation
        text = re.sub(r'\s+([.,:;!?])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def should_preprocess(self, transcript: str, threshold_words: int = 3000) -> bool:
        """Determine if transcript should be preprocessed based on size."""
        word_count = len(transcript.split())
        return word_count > threshold_words 