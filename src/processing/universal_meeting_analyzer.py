"""
Universal Meeting Intelligence System
Implements adaptive meeting analysis with automatic type detection and content-adaptive extraction.
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)

class MeetingType(Enum):
    """Supported meeting types for adaptive analysis"""
    TECHNICAL = "technical"
    STRATEGY = "strategy" 
    ALIGNMENT = "alignment"
    ONE_ON_ONE = "one_on_one"
    STANDUP = "standup"
    GENERAL_SYNC = "general_sync"

@dataclass
class MeetingContext:
    """Context information about a meeting"""
    title: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    duration_estimate: Optional[int] = None  # minutes
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    folder_path: Optional[str] = None
    booking_team: Optional[str] = None
    participant_roles: Dict[str, str] = field(default_factory=dict)

@dataclass
class MeetingAnalysis:
    """Result of meeting analysis"""
    meeting_type: MeetingType
    confidence: float
    summary: str
    key_points: List[str]
    action_items: List[str]
    participants: List[str]
    context: MeetingContext
    quality_indicators: Dict[str, Any]

class MeetingTypeDetector:
    """Detects meeting type from content and metadata"""
    
    def __init__(self):
        self.patterns = {
            MeetingType.TECHNICAL: {
                'keywords': ['architecture', 'api', 'system', 'service', 'database', 'deployment', 
                           'code', 'implementation', 'technical', 'integration', 'infrastructure',
                           'backend', 'frontend', 'microservice', 'repository', 'framework'],
                'phrases': ['system design', 'code review', 'technical decision', 'api design',
                          'architecture decision', 'technical debt', 'performance issue']
            },
            MeetingType.STRATEGY: {
                'keywords': ['roadmap', 'strategy', 'planning', 'objectives', 'goals', 'business',
                           'priorities', 'vision', 'direction', 'budget', 'resources', 'timeline',
                           'milestone', 'deliverable', 'quarter', 'okr', 'q1', 'q2', 'q3', 'q4',
                           'allocate', 'prioritize', 'market', 'opportunity', 'initiative'],
                'phrases': ['business goals', 'strategic direction', 'product roadmap', 'quarterly planning',
                          'business case', 'market opportunity', 'resource allocation', 'business objectives',
                          'key objectives', 'business decisions', 'strategic decisions']
            },
            MeetingType.ALIGNMENT: {
                'keywords': ['coordination', 'sync', 'dependencies', 'blockers', 'teams', 'alignment',
                           'handoff', 'collaboration', 'communication', 'update', 'status',
                           'cross-team', 'integration', 'workflow', 'coordinate', 'blocked'],
                'phrases': ['cross-team', 'team coordination', 'sync up', 'alignment meeting',
                          'dependency management', 'team sync', 'better coordination', 'need alignment',
                          'communication protocols', 'handoff process']
            },
            MeetingType.ONE_ON_ONE: {
                'keywords': ['career', 'feedback', 'development', 'performance', 'personal', 'growth',
                           'promotion', 'goals', 'coaching', 'mentoring', 'review', 'one-on-one',
                           'individual', 'pdp', 'feeling', 'opportunities', 'skills'],
                'phrases': ['career development', 'performance review', 'personal goals', '1:1',
                          'career path', 'professional development', 'how are you feeling',
                          'leadership opportunities', 'growth opportunity', 'promotion track']
            },
            MeetingType.STANDUP: {
                'keywords': ['yesterday', 'today', 'tomorrow', 'blocked', 'blocker', 'status',
                           'progress', 'standup', 'daily', 'scrum', 'sprint', 'working on',
                           'completed', 'next', 'stuck', 'finished', 'focusing'],
                'phrases': ['daily standup', 'what I worked on', 'what I\'m working on', 
                          'blockers', 'yesterday I', 'today I will', 'I worked on', 'I completed',
                          'I\'m focusing on', 'I finished', 'help with']
            }
        }
        
        self.booking_context = {
            'teams': ['flights', 'accommodations', 'attractions', 'ground transport', 'payments',
                     'user experience', 'platform', 'data', 'mobile', 'web'],
            'roles': {'em': 'Engineering Manager', 'pm': 'Product Manager', 'tl': 'Tech Lead',
                     'swe': 'Software Engineer', 'ds': 'Data Scientist', 'ux': 'UX Designer'},
            'business_terms': ['supplier', 'booking flow', 'conversion', 'user journey',
                             'inventory', 'pricing', 'search', 'recommendations']
        }

    def detect_meeting_type(self, transcript: str, context: MeetingContext) -> Tuple[MeetingType, float]:
        """
        Detect meeting type from transcript content and metadata context
        Returns (MeetingType, confidence_score)
        """
        # Normalize transcript for analysis
        content_lower = transcript.lower()
        
        # Calculate scores for each meeting type
        type_scores = {}
        
        for meeting_type, patterns in self.patterns.items():
            score = self._calculate_content_score(content_lower, patterns)
            
            # Apply metadata boost
            metadata_boost = self._calculate_metadata_boost(meeting_type, context)
            
            # Apply Booking.com context boost
            booking_boost = self._calculate_booking_boost(content_lower, meeting_type)
            
            final_score = score * (1 + metadata_boost + booking_boost)
            type_scores[meeting_type] = final_score
            
            logger.debug(f"{meeting_type.value}: content={score:.2f}, metadata_boost={metadata_boost:.2f}, "
                        f"booking_boost={booking_boost:.2f}, final={final_score:.2f}")
        
        # Determine best match
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        
        # Calculate confidence (normalize score to 0-1 range)
        max_possible_score = 20.0  # Increased due to higher scoring weights
        confidence = min(best_score / max_possible_score, 1.0)
        
        # If confidence is too low, default to GENERAL_SYNC
        if confidence < 0.15:  # Lowered threshold
            return MeetingType.GENERAL_SYNC, confidence
            
        return best_type, confidence

    def _calculate_content_score(self, content: str, patterns: Dict[str, List[str]]) -> float:
        """Calculate score based on keyword and phrase matches"""
        score = 0.0
        
        # Keyword scoring with higher weights
        for keyword in patterns['keywords']:
            count = content.count(keyword)
            score += count * 0.5  # Increased from 0.1 to 0.5
            
        # Phrase scoring (much higher weight)
        for phrase in patterns['phrases']:
            count = content.count(phrase)
            score += count * 1.0  # Increased from 0.3 to 1.0
            
        return score

    def _calculate_metadata_boost(self, meeting_type: MeetingType, context: MeetingContext) -> float:
        """Calculate score boost based on meeting metadata"""
        boost = 0.0
        
        # Title-based detection
        if context.title:
            title_lower = context.title.lower()
            if meeting_type == MeetingType.STANDUP and any(word in title_lower for word in ['standup', 'daily', 'scrum']):
                boost += 0.5
            elif meeting_type == MeetingType.ONE_ON_ONE and any(word in title_lower for word in ['1:1', 'one-on-one', 'career']):
                boost += 0.5
            elif meeting_type == MeetingType.TECHNICAL and any(word in title_lower for word in ['architecture', 'technical', 'design', 'review']):
                boost += 0.3
            elif meeting_type == MeetingType.STRATEGY and any(word in title_lower for word in ['strategy', 'planning', 'roadmap']):
                boost += 0.3
        
        # Participant count heuristics
        if context.participants:
            participant_count = len(context.participants)
            if meeting_type == MeetingType.ONE_ON_ONE and participant_count == 2:
                boost += 0.3
            elif meeting_type == MeetingType.STANDUP and 3 <= participant_count <= 8:
                boost += 0.2
            elif meeting_type == MeetingType.ALIGNMENT and participant_count > 8:
                boost += 0.2
        
        # Time-based heuristics
        if context.time_of_day:
            if meeting_type == MeetingType.STANDUP and context.time_of_day in ['morning']:
                boost += 0.2
            elif meeting_type == MeetingType.ONE_ON_ONE and context.time_of_day in ['afternoon'] and context.day_of_week == 'friday':
                boost += 0.2
                
        return boost

    def _calculate_booking_boost(self, content: str, meeting_type: MeetingType) -> float:
        """Calculate score boost based on Booking.com specific context"""
        boost = 0.0
        
        # Team context detection
        for team in self.booking_context['teams']:
            if team in content:
                if meeting_type == MeetingType.TECHNICAL and team in ['platform', 'data']:
                    boost += 0.1
                elif meeting_type == MeetingType.STRATEGY and team in ['flights', 'accommodations']:
                    boost += 0.1
                    
        # Business terms
        business_term_count = sum(1 for term in self.booking_context['business_terms'] if term in content)
        if business_term_count > 0:
            if meeting_type == MeetingType.STRATEGY:
                boost += business_term_count * 0.05
            elif meeting_type == MeetingType.TECHNICAL:
                boost += business_term_count * 0.03
                
        return boost

class AdaptivePromptBuilder:
    """Builds meeting type-specific prompts for better analysis"""
    
    def __init__(self):
        self.base_template = self._load_base_template()
        
    def _load_base_template(self) -> str:
        """Load the universal meeting prompt template"""
        return """You are an expert meeting analyst specialized in {company_context}. Your job is to create useful summaries for any type of meeting.

MEETING CONTEXT:
- Type: {meeting_type}
- Company: Booking.com Engineering
- Participants: {participants}
{additional_context}

STEP 1: Confirm the meeting type and participants
STEP 2: Extract information most relevant to this meeting type
STEP 3: Format in a consistent, scannable structure

{type_specific_instructions}

OUTPUT FORMAT:
# Meeting Summary: {meeting_type_display}

**Meeting Info:**
- Date: {date}
- Participants: {participants_list}
- Type: {meeting_type_display}
- Duration: ~{duration} minutes

## 🎯 Key Outcomes
{outcomes_instruction}

## 📋 Main Discussion Points
{discussion_points_instruction}

## ✅ Action Items
{action_items_instruction}

## 🔄 Follow-ups & Next Steps
{followups_instruction}

## ⚠️ Blockers & Concerns
{blockers_instruction}

---

IMPORTANT RULES:
1. Use exact quotes for technical terms, system names, and business metrics
2. Don't invent information not in the transcript
3. Focus on information most relevant to {meeting_type} meetings
4. If action items aren't clear, note "Action items unclear - follow up needed"
5. Prioritize Booking.com specific context (teams, products, business metrics)

TRANSCRIPT:
{transcript}"""

    def build_prompt(self, meeting_type: MeetingType, context: MeetingContext, transcript: str) -> str:
        """Build adaptive prompt based on meeting type and context"""
        
        # Get type-specific instructions
        type_instructions = self._get_type_specific_instructions(meeting_type)
        
        # Format participants
        participants_str = ", ".join(context.participants) if context.participants else "Not specified"
        
        # Build additional context
        additional_context = self._build_additional_context(context)
        
        # Format the prompt
        prompt = self.base_template.format(
            company_context="Booking.com Engineering meetings",
            meeting_type=meeting_type.value,
            meeting_type_display=meeting_type.value.replace('_', ' ').title(),
            participants=participants_str,
            participants_list=participants_str,
            additional_context=additional_context,
            type_specific_instructions=type_instructions['instructions'],
            date="[Extract from transcript or context]",
            duration=context.duration_estimate or "[Estimate from content]",
            outcomes_instruction=type_instructions['outcomes'],
            discussion_points_instruction=type_instructions['discussion_points'],
            action_items_instruction=type_instructions['action_items'],
            followups_instruction=type_instructions['followups'],
            blockers_instruction=type_instructions['blockers'],
            transcript=transcript
        )
        
        return prompt

    def _get_type_specific_instructions(self, meeting_type: MeetingType) -> Dict[str, str]:
        """Get specialized instructions for each meeting type"""
        
        instructions = {
            MeetingType.TECHNICAL: {
                'instructions': """FOR TECHNICAL MEETINGS:
Focus on:
- Systems/APIs/technologies discussed
- Architecture decisions made
- Technical challenges identified
- Implementation approaches
- Code review feedback
- Technical debt discussions
- Performance considerations""",
                'outcomes': '[2-3 sentence summary of technical decisions and next steps]',
                'discussion_points': '[Bullet points of technical topics: systems discussed, decisions made, technical challenges]',
                'action_items': '[Technical tasks, code reviews, implementation work with owners and timelines]',
                'followups': '[Technical follow-ups, additional design work, code review schedules]',
                'blockers': '[Technical blockers, dependency issues, infrastructure problems]'
            },
            
            MeetingType.STRATEGY: {
                'instructions': """FOR STRATEGY MEETINGS:
Focus on:
- Goals and objectives
- Business decisions
- Resource allocation
- Timeline and milestones
- Business metrics and targets
- Product direction
- Market opportunities""",
                'outcomes': '[2-3 sentence summary of strategic decisions and business direction]',
                'discussion_points': '[Strategic topics: business goals, product direction, resource decisions]',
                'action_items': '[Strategic tasks with owners, timelines, and success metrics]',
                'followups': '[Strategic planning sessions, business reviews, metric tracking]',
                'blockers': '[Business blockers, resource constraints, market challenges]'
            },
            
            MeetingType.ALIGNMENT: {
                'instructions': """FOR ALIGNMENT MEETINGS:
Focus on:
- Dependencies between teams
- Coordination points
- Blockers and their owners
- Communication protocols
- Cross-team handoffs
- Workflow coordination""",
                'outcomes': '[2-3 sentence summary of alignment agreements and coordination plans]',
                'discussion_points': '[Coordination topics: team dependencies, handoff processes, communication needs]',
                'action_items': '[Coordination tasks, communication improvements, dependency resolution]',
                'followups': '[Regular sync meetings, dependency check-ins, coordination reviews]',
                'blockers': '[Cross-team blockers, communication gaps, dependency issues]'
            },
            
            MeetingType.ONE_ON_ONE: {
                'instructions': """FOR 1:1 MEETINGS:
Focus on:
- Performance feedback
- Career development topics
- Personal concerns or goals
- Manager guidance
- Growth opportunities
- Individual challenges""",
                'outcomes': '[2-3 sentence summary of career discussion and personal development focus]',
                'discussion_points': '[Personal development topics: career goals, feedback, growth opportunities]',
                'action_items': '[Personal development tasks, career actions, skill building activities]',
                'followups': '[Career development check-ins, skill assessment, growth plan reviews]',
                'blockers': '[Personal blockers, skill gaps, career progression challenges]'
            },
            
            MeetingType.STANDUP: {
                'instructions': """FOR STANDUP MEETINGS:
Focus on:
- Work completed
- Current focus
- Blockers needing help
- Next priorities
- Sprint progress
- Team coordination""",
                'outcomes': '[2-3 sentence summary of team progress and immediate priorities]',
                'discussion_points': '[Status updates: completed work, current tasks, team progress]',
                'action_items': '[Immediate tasks, blocker resolution, sprint commitments]',
                'followups': '[Daily coordination, sprint planning, blocker resolution]',
                'blockers': '[Individual blockers, team impediments, immediate help needed]'
            },
            
            MeetingType.GENERAL_SYNC: {
                'instructions': """FOR GENERAL SYNC MEETINGS:
Focus on:
- Key updates shared
- Decisions requiring follow-up
- Information flow between teams
- General coordination
- Mixed topics discussed""",
                'outcomes': '[2-3 sentence summary of key updates and decisions]',
                'discussion_points': '[General topics: updates, decisions, information sharing]',
                'action_items': '[Various tasks and follow-ups identified]',
                'followups': '[Regular coordination, information sharing, decision follow-ups]',
                'blockers': '[General blockers and coordination issues]'
            }
        }
        
        return instructions.get(meeting_type, instructions[MeetingType.GENERAL_SYNC])

    def _build_additional_context(self, context: MeetingContext) -> str:
        """Build additional context information"""
        context_parts = []
        
        if context.title:
            context_parts.append(f"- Meeting Title: {context.title}")
            
        if context.booking_team:
            context_parts.append(f"- Team: {context.booking_team}")
            
        if context.duration_estimate:
            context_parts.append(f"- Duration: ~{context.duration_estimate} minutes")
            
        if context.time_of_day and context.day_of_week:
            context_parts.append(f"- Timing: {context.day_of_week} {context.time_of_day}")
            
        return "\n".join(context_parts) if context_parts else "- No additional context available"

class UniversalMeetingAnalyzer:
    """Main class for universal meeting intelligence"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.detector = MeetingTypeDetector()
        self.prompt_builder = AdaptivePromptBuilder()
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration for the analyzer"""
        default_config = {
            'confidence_threshold': 0.3,
            'enable_booking_context': True,
            'default_meeting_type': 'general_sync'
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config.get('universal_meeting_analyzer', {}))
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
                
        return default_config

    def analyze_meeting(self, transcript: str, metadata: Dict[str, Any] = None) -> MeetingAnalysis:
        """
        Main method to analyze a meeting transcript with adaptive intelligence
        """
        # Build meeting context
        context = self._build_meeting_context(metadata or {})
        
        # Detect meeting type
        meeting_type, confidence = self.detector.detect_meeting_type(transcript, context)
        
        logger.info(f"Detected meeting type: {meeting_type.value} (confidence: {confidence:.2f})")
        
        # Build adaptive prompt
        prompt = self.prompt_builder.build_prompt(meeting_type, context, transcript)
        
        # For now, return the prompt and basic analysis
        # This will be integrated with AI providers in the next phase
        return MeetingAnalysis(
            meeting_type=meeting_type,
            confidence=confidence,
            summary=f"[Adaptive summary for {meeting_type.value} meeting - to be generated by AI provider]",
            key_points=[f"Key points extraction pending AI provider integration"],
            action_items=[f"Action items extraction pending AI provider integration"],
            participants=context.participants or [],
            context=context,
            quality_indicators={
                'meeting_type_confidence': confidence,
                'has_adaptive_prompt': True,
                'prompt_length': len(prompt)
            }
        )

    def _build_meeting_context(self, metadata: Dict[str, Any]) -> MeetingContext:
        """Build meeting context from available metadata"""
        
        # Extract participants from transcript or metadata
        participants = self._extract_participants(metadata)
        
        # Extract meeting title from folder path or metadata
        title = self._extract_meeting_title(metadata)
        
        # Detect Booking.com team context
        booking_team = self._detect_booking_team(metadata, title)
        
        # Extract timing information
        time_info = self._extract_time_info(metadata)
        
        return MeetingContext(
            title=title,
            participants=participants,
            duration_estimate=metadata.get('duration_estimate'),
            time_of_day=time_info.get('time_of_day'),
            day_of_week=time_info.get('day_of_week'),
            folder_path=metadata.get('folder_path'),
            booking_team=booking_team,
            participant_roles=self._extract_participant_roles(participants)
        )

    def _extract_participants(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract participant names from metadata"""
        participants = []
        
        # Try various metadata fields
        if 'participants' in metadata:
            participants = metadata['participants']
        elif 'attendees' in metadata:
            participants = metadata['attendees']
        elif 'speakers' in metadata:
            participants = metadata['speakers']
            
        return participants if isinstance(participants, list) else []

    def _extract_meeting_title(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract meeting title from metadata or folder path"""
        
        # Try direct title field
        if 'title' in metadata:
            return metadata['title']
            
        # Try to extract from folder path
        if 'folder_path' in metadata:
            folder_path = metadata['folder_path']
            # Extract folder name as potential meeting title
            import os
            folder_name = os.path.basename(folder_path)
            if folder_name and folder_name != 'Zoom':
                return folder_name
                
        return None

    def _detect_booking_team(self, metadata: Dict[str, Any], title: Optional[str]) -> Optional[str]:
        """Detect which Booking.com team this meeting belongs to"""
        
        search_text = ""
        if title:
            search_text += title.lower() + " "
        if 'folder_path' in metadata:
            search_text += metadata['folder_path'].lower() + " "
            
        # Check for team indicators
        for team in self.detector.booking_context['teams']:
            if team in search_text:
                return team.title()
                
        return None

    def _extract_time_info(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract timing information for heuristics"""
        time_info = {}
        
        # This would be implemented based on actual metadata structure
        # For now, return empty dict
        return time_info

    def _extract_participant_roles(self, participants: List[str]) -> Dict[str, str]:
        """Extract participant roles from names or email addresses"""
        roles = {}
        
        for participant in participants:
            # Look for role indicators in names/emails
            participant_lower = participant.lower()
            for role_abbr, role_full in self.detector.booking_context['roles'].items():
                if role_abbr in participant_lower:
                    roles[participant] = role_full
                    break
                    
        return roles

    def get_adaptive_prompt(self, transcript: str, metadata: Dict[str, Any] = None) -> str:
        """Get the adaptive prompt that would be used for this meeting"""
        context = self._build_meeting_context(metadata or {})
        meeting_type, _ = self.detector.detect_meeting_type(transcript, context)
        return self.prompt_builder.build_prompt(meeting_type, context, transcript) 