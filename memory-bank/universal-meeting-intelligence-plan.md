# Universal Meeting Intelligence System Implementation Plan

## 🎯 Overview
Creating a general-purpose meeting intelligence system that automatically adapts to different meeting types, eliminating the need for manual configuration or separate templates. This system will replace our current generic summarization approach with intelligent, context-aware processing.

## 🧠 Core Concept: Adaptive Intelligence
Following Anthropic's two-stage approach:
1. **Meeting Type Detection** - Automatically identify what kind of meeting it is
2. **Content-Adaptive Extraction** - Extract information most relevant to that meeting type

## 📋 Meeting Types to Support

### Primary Meeting Types
- **Technical/Architecture**: System design, code reviews, technical decisions, API discussions
- **Strategy/Planning**: Roadmaps, objectives, business decisions, feature planning
- **Alignment**: Cross-team coordination, dependencies, blockers, sync meetings
- **1:1**: Personal development, feedback, career discussions, performance reviews
- **Standup**: Status updates, blockers, next steps, daily coordination
- **General Sync**: Mixed topics, updates, information sharing

### Booking.com Specific Contexts
- **Flights Engineering**: Supplier integrations, booking flows, payment systems
- **Product Strategy**: User experience, business metrics, feature prioritization
- **Engineering Management**: Team processes, career development, organizational topics
- **Operational**: Incident reviews, deployment discussions, process improvements

## 🔄 Implementation Phases

### Phase 1: Universal Prompt System (Week 1)
**Goal**: Replace current generic prompts with adaptive intelligence

#### Deliverables:
- [ ] Universal meeting prompt template
- [ ] Meeting type detection logic
- [ ] Content-adaptive extraction system
- [ ] Booking.com context integration

#### Technical Implementation:
- Create `UniversalMeetingAnalyzer` class
- Implement meeting type detection algorithm
- Build adaptive prompt construction
- Add Booking.com specific enhancements

#### Success Criteria:
- System automatically detects meeting type with 80%+ accuracy
- Summaries are contextually relevant to meeting type
- No manual configuration required per meeting

### Phase 2: Context Enhancement (Week 2)
**Goal**: Add smart context detection from meeting metadata

#### Deliverables:
- [ ] Meeting title context extraction
- [ ] Participant role detection
- [ ] Time-based meeting pattern recognition
- [ ] Content length adaptation

#### Technical Implementation:
- Parse Zoom folder names for meeting context
- Extract participant roles from names/emails
- Implement time-based heuristics
- Add meeting duration-based adaptations

#### Success Criteria:
- Meeting context correctly identified from metadata
- Participant roles automatically recognized
- Time patterns improve meeting type detection

### Phase 3: Quality Assessment Integration (Week 3)
**Goal**: Integrate quality assessment with meeting type awareness

#### Deliverables:
- [ ] Meeting type-specific quality metrics
- [ ] Adaptive quality thresholds
- [ ] Quality feedback system
- [ ] Performance monitoring

#### Technical Implementation:
- Extend QualityAssessor for meeting-type awareness
- Define quality metrics per meeting type
- Implement adaptive scoring
- Add quality improvement suggestions

#### Success Criteria:
- Quality assessment adapts to meeting type expectations
- Quality scores improve significantly across all meeting types
- System provides actionable quality feedback

### Phase 4: Testing & Optimization (Week 4)
**Goal**: Comprehensive testing and performance optimization

#### Deliverables:
- [ ] Meeting type detection accuracy testing
- [ ] Cross-meeting-type quality comparison
- [ ] Performance benchmarking
- [ ] User feedback integration

#### Technical Implementation:
- Create comprehensive test suite
- Implement A/B testing framework
- Performance profiling and optimization
- User feedback collection system

#### Success Criteria:
- 90%+ meeting type detection accuracy
- Consistent high-quality summaries across all types
- Performance maintains current processing speeds

## 🛠 Technical Architecture

### Core Components

#### 1. UniversalMeetingAnalyzer
```python
class UniversalMeetingAnalyzer:
    def analyze_meeting(self, transcript: str, metadata: dict) -> MeetingAnalysis
    def detect_meeting_type(self, content: str, metadata: dict) -> MeetingType
    def generate_adaptive_summary(self, transcript: str, meeting_type: MeetingType) -> Summary
```

#### 2. MeetingTypeDetector
```python
class MeetingTypeDetector:
    def detect_from_content(self, transcript: str) -> MeetingType
    def detect_from_metadata(self, metadata: dict) -> MeetingType
    def apply_booking_context(self, detected_type: MeetingType, content: str) -> MeetingType
```

#### 3. AdaptivePromptBuilder
```python
class AdaptivePromptBuilder:
    def build_prompt(self, meeting_type: MeetingType, context: dict) -> str
    def add_booking_context(self, prompt: str, meeting_type: MeetingType) -> str
    def customize_for_participants(self, prompt: str, participants: list) -> str
```

### Meeting Type Detection Algorithm

#### Pattern Matching Rules:
- **Technical Keywords**: "architecture", "API", "system", "code", "deployment", "service"
- **Strategy Keywords**: "roadmap", "objectives", "business", "goals", "planning", "strategy"
- **Alignment Keywords**: "dependencies", "coordination", "sync", "blockers", "teams"
- **1:1 Keywords**: "career", "feedback", "development", "performance", "personal"
- **Standup Keywords**: "yesterday", "today", "tomorrow", "blocked", "status", "progress"

#### Metadata Heuristics:
- **Time patterns**: Morning (standups), Friday PM (1:1s), Long meetings (technical/strategy)
- **Participant count**: 2 people (likely 1:1), 3-8 people (team meetings), 8+ (alignment)
- **Meeting title patterns**: "Architecture Review", "Weekly Sync", "Career Chat"

#### Booking.com Context Clues:
- **Team identifiers**: "Flights", "Accommodations", "Attractions", "Ground Transport"
- **Role indicators**: "EM" (Engineering Manager), "PM" (Product Manager), "TL" (Tech Lead)
- **Business context**: "supplier", "booking flow", "payment", "user experience"

## 📊 Expected Quality Improvements

### Before (Current State):
- Generic summaries regardless of meeting type
- 20-40% relevance to actual meeting content
- Missing context-specific information
- No adaptation to participant needs

### After (Universal Intelligence):
- **Meeting Type Detection**: 90%+ accuracy
- **Content Relevance**: 80-95% depending on meeting type
- **Context Awareness**: Full integration of Booking.com specific context
- **Adaptive Quality**: Different quality metrics per meeting type

### Meeting Type Specific Improvements:

#### Technical Meetings:
- **Before**: "Team discussed various topics and made some decisions"
- **After**: "Architecture decision: Selected service-based approach over modular for multiplier system. Key technical concerns: API versioning strategy and database migration timeline."

#### Strategy Meetings:
- **Before**: "Team talked about future plans and priorities"
- **After**: "Q4 Flights roadmap prioritized: 1) Supplier diversity expansion (reduce dependency risk), 2) Mobile booking flow optimization (targeting 15% conversion improvement), 3) Payment processing redundancy"

#### 1:1 Meetings:
- **Before**: "Manager and team member had discussion about work"
- **After**: "Career development focus: Senior Engineer promotion track discussion. Feedback on technical leadership opportunities. Action: Shadow architect role in Q1, lead API design review next sprint."

## 🔧 Integration Points

### Current System Integration:
- Maintains compatibility with existing `TranscriptProcessor`
- Plugs into current file monitoring system
- Uses existing output formatting structure
- Preserves all current configuration options

### Future Cloud Integration:
- Universal prompts will work with both Ollama and Claude
- Meeting type detection will inform provider selection
- Quality assessment will be meeting-type aware
- Adaptive processing will optimize for each provider's strengths

## 📈 Success Metrics

### Technical Metrics:
- Meeting type detection accuracy: >90%
- Processing time: Maintain current performance
- Quality scores: Improve from 40% to 80%+ average
- User satisfaction: Measure through feedback system

### Business Impact:
- Reduced time to find relevant meeting information
- Better action item tracking across meeting types
- Improved meeting follow-up effectiveness
- Enhanced cross-team coordination

## 🚀 Next Steps

1. **Immediate**: Implement Phase 1 (Universal Prompt System)
2. **Week 2**: Add context enhancement features
3. **Week 3**: Integrate with quality assessment system
4. **Week 4**: Comprehensive testing and optimization
5. **Future**: Cloud integration with adaptive intelligence

## 📝 Notes

- This system replaces the need for multiple prompt templates
- All meeting types handled by single, adaptive system
- Booking.com context integrated throughout
- Maintains backward compatibility
- Prepares foundation for hybrid cloud integration

---

*This plan addresses the core quality issues by making the AI system contextually aware rather than generically processing all meetings the same way.* 