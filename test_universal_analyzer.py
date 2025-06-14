#!/usr/bin/env python3
"""
Test script for Universal Meeting Intelligence System
Tests meeting type detection and adaptive prompt generation across different meeting types.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from processing.universal_meeting_analyzer import (
    UniversalMeetingAnalyzer, 
    MeetingType, 
    MeetingContext
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test transcripts for different meeting types
TEST_TRANSCRIPTS = {
    "technical": """
    Speaker 1: Alright, let's talk about the architecture decision for the multiplier system. 
    We need to decide between service-based architecture versus modular architecture approach.
    
    Speaker 2: The service-based approach would give us better scalability, but the modular 
    approach might be easier to implement initially. What are the implications for the API design?
    
    Speaker 1: With service-based, we'd need to design proper microservice interfaces. 
    The database migration would also be more complex. Let's also consider the performance 
    implications and technical debt we might be taking on.
    
    Speaker 2: I think we should go with service-based for long-term maintainability. 
    We can implement it in phases to reduce risk.
    """,
    
    "strategy": """
    Speaker 1: Let's review our Q4 roadmap for the Flights product. We need to prioritize 
    our key business objectives and allocate resources accordingly.
    
    Speaker 2: Our main goals are supplier diversity expansion, mobile booking flow optimization, 
    and payment processing redundancy. The business case shows we could improve conversion by 15%.
    
    Speaker 1: Great. What's our timeline for these milestones? And what budget allocation 
    are we looking at for each initiative?
    
    Speaker 2: Supplier diversity is our highest priority due to market opportunity. 
    We should target Q1 delivery with dedicated team resources.
    """,
    
    "alignment": """
    Speaker 1: We need better coordination between our teams. There are dependencies 
    between the Flights API and the Payment processing team that are causing blockers.
    
    Speaker 2: Yes, we're blocked on the integration because we need the new authentication 
    flow from Platform team. The handoff process isn't clear.
    
    Speaker 3: Let's establish better communication protocols. We should have regular 
    sync meetings to track cross-team dependencies and resolve workflow issues.
    
    Speaker 1: Agreed. We need alignment on the timeline and clear ownership of each component.
    """,
    
    "one_on_one": """
    Speaker 1: How are you feeling about your career development goals this quarter?
    
    Speaker 2: I'm interested in taking on more technical leadership opportunities. 
    The feedback from the last performance review was helpful.
    
    Speaker 1: That's great to hear. I think you'd be a good fit to shadow the architect role 
    in the next project. We could also look at promoting you to Senior Engineer next year.
    
    Speaker 2: That sounds like a great growth opportunity. What skills should I focus on 
    developing for the promotion track?
    
    Speaker 1: Let's work on your mentoring abilities and system design skills. 
    I'll make sure you get more visibility in the team.
    """,
    
    "standup": """
    Speaker 1: Yesterday I worked on the API integration testing. Today I'm focusing on 
    the database migration scripts. No blockers currently.
    
    Speaker 2: I completed the frontend components yesterday. Today I'm working on 
    the user authentication flow. I'm blocked on getting access to the staging environment.
    
    Speaker 3: Yesterday I finished the code review for the payment module. Today I'll 
    start on the deployment automation. I need help with the Docker configuration.
    
    Speaker 1: I can help you with Docker after standup. Let's sync up on that.
    """,
    
    "general": """
    Speaker 1: Let's start with some general updates from each team.
    
    Speaker 2: Platform team shipped the new logging framework last week. 
    This should help with debugging across all services.
    
    Speaker 3: Accommodations team is seeing good metrics on the new search feature. 
    We're planning to roll it out to more markets next month.
    
    Speaker 1: Good to hear. Any concerns or issues we should be aware of?
    
    Speaker 2: Just the usual deployment coordination. We should make sure everyone 
    is aligned on the release schedule.
    """
}

# Test metadata for different scenarios
TEST_METADATA = {
    "technical": {
        "participants": ["John Smith (TL)", "Alice Chen (SWE)", "Bob Wilson (Architect)"],
        "title": "Architecture Review - Multiplier System",
        "folder_path": "/Users/test/Documents/Zoom/Tech Architecture Meeting",
        "duration_estimate": 60
    },
    
    "strategy": {
        "participants": ["Sarah Johnson (PM)", "Mike Davis (EM)"],
        "title": "Q4 Flights Roadmap Planning",
        "folder_path": "/Users/test/Documents/Zoom/Quarterly Planning",
        "duration_estimate": 90
    },
    
    "alignment": {
        "participants": ["Team Lead A", "Team Lead B", "Team Lead C", "Engineering Manager"],
        "title": "Cross-team Sync",
        "folder_path": "/Users/test/Documents/Zoom/Team Alignment",
        "duration_estimate": 45
    },
    
    "one_on_one": {
        "participants": ["Manager", "Direct Report"],
        "title": "Career Development 1:1",
        "folder_path": "/Users/test/Documents/Zoom/Weekly 1-1",
        "duration_estimate": 30
    },
    
    "standup": {
        "participants": ["Dev 1", "Dev 2", "Dev 3", "Scrum Master"],
        "title": "Daily Standup",
        "folder_path": "/Users/test/Documents/Zoom/Daily Standup",
        "duration_estimate": 15
    },
    
    "general": {
        "participants": ["Platform Lead", "Accommodations Lead", "Flights Lead"],
        "title": "Weekly Team Updates",
        "folder_path": "/Users/test/Documents/Zoom/Weekly Sync",
        "duration_estimate": 30
    }
}

def test_meeting_type_detection():
    """Test meeting type detection accuracy"""
    print("🧠 Testing Meeting Type Detection")
    print("=" * 50)
    
    analyzer = UniversalMeetingAnalyzer()
    
    detection_results = {}
    
    for expected_type, transcript in TEST_TRANSCRIPTS.items():
        metadata = TEST_METADATA.get(expected_type, {})
        
        # Analyze the meeting
        analysis = analyzer.analyze_meeting(transcript, metadata)
        
        # Check if detected type matches expected
        detected_type = analysis.meeting_type.value
        confidence = analysis.confidence
        
        is_correct = (
            (expected_type == "technical" and detected_type == "technical") or
            (expected_type == "strategy" and detected_type == "strategy") or
            (expected_type == "alignment" and detected_type == "alignment") or
            (expected_type == "one_on_one" and detected_type == "one_on_one") or
            (expected_type == "standup" and detected_type == "standup") or
            (expected_type == "general" and detected_type == "general_sync")
        )
        
        detection_results[expected_type] = {
            'detected': detected_type,
            'confidence': confidence,
            'correct': is_correct
        }
        
        status = "✅ CORRECT" if is_correct else "❌ INCORRECT"
        print(f"{expected_type.upper():12} → {detected_type:12} (confidence: {confidence:.2f}) {status}")
    
    # Calculate accuracy
    correct_count = sum(1 for r in detection_results.values() if r['correct'])
    total_count = len(detection_results)
    accuracy = correct_count / total_count * 100
    
    print(f"\n📊 Detection Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
    
    return detection_results

def test_adaptive_prompts():
    """Test adaptive prompt generation for different meeting types"""
    print("\n🎯 Testing Adaptive Prompt Generation")
    print("=" * 50)
    
    analyzer = UniversalMeetingAnalyzer()
    
    for meeting_type, transcript in TEST_TRANSCRIPTS.items():
        metadata = TEST_METADATA.get(meeting_type, {})
        
        # Get the adaptive prompt
        prompt = analyzer.get_adaptive_prompt(transcript, metadata)
        
        # Extract key sections from prompt
        has_type_specific = f"FOR {meeting_type.upper()}" in prompt.upper()
        has_booking_context = "Booking.com" in prompt
        has_participants = any(p in prompt for p in metadata.get('participants', []))
        
        print(f"\n{meeting_type.upper()} Meeting Prompt:")
        print(f"  📝 Length: {len(prompt)} characters")
        print(f"  🎯 Type-specific instructions: {'✅' if has_type_specific else '❌'}")
        print(f"  🏢 Booking context: {'✅' if has_booking_context else '❌'}")
        print(f"  👥 Participant info: {'✅' if has_participants else '❌'}")
        
        # Show a snippet of the type-specific instructions
        if "FOR " in prompt.upper():
            start = prompt.upper().find("FOR ")
            end = prompt.find("\n", start + 100) if prompt.find("\n", start + 100) > 0 else start + 200
            snippet = prompt[start:end].strip()
            print(f"  💡 Instructions: {snippet[:100]}...")

def test_booking_context_detection():
    """Test Booking.com specific context detection"""
    print("\n🏢 Testing Booking.com Context Detection")
    print("=" * 50)
    
    analyzer = UniversalMeetingAnalyzer()
    
    # Test transcript with Booking.com specific terms
    booking_transcript = """
    Speaker 1: The flights supplier integration is having issues with the booking flow. 
    We need to improve our conversion rates and user journey optimization.
    
    Speaker 2: Yes, our inventory management system needs better pricing algorithms. 
    The search functionality is also impacting our recommendations engine.
    
    Speaker 1: Let's coordinate with the accommodations team on this. They've had 
    similar challenges with supplier diversity.
    """
    
    booking_metadata = {
        "participants": ["John (EM Flights)", "Sarah (PM Platform)"],
        "title": "Flights Supplier Integration Review",
        "folder_path": "/Users/test/Documents/Zoom/Flights Team Meeting"
    }
    
    analysis = analyzer.analyze_meeting(booking_transcript, booking_metadata)
    
    print(f"Meeting Type: {analysis.meeting_type.value}")
    print(f"Confidence: {analysis.confidence:.2f}")
    print(f"Detected Team: {analysis.context.booking_team}")
    
    # Check for business terms detection
    prompt = analyzer.get_adaptive_prompt(booking_transcript, booking_metadata)
    business_terms = ['supplier', 'booking flow', 'conversion', 'inventory', 'pricing']
    detected_terms = [term for term in business_terms if term in booking_transcript.lower()]
    
    print(f"Business Terms Detected: {', '.join(detected_terms)}")
    print(f"Booking Context in Prompt: {'✅' if 'Booking.com' in prompt else '❌'}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n⚠️  Testing Edge Cases")
    print("=" * 50)
    
    analyzer = UniversalMeetingAnalyzer()
    
    # Test with minimal content
    minimal_transcript = "Hello. How are you? That's good. Okay, bye."
    analysis = analyzer.analyze_meeting(minimal_transcript)
    print(f"Minimal content → {analysis.meeting_type.value} (confidence: {analysis.confidence:.2f})")
    
    # Test with empty metadata
    empty_metadata = {}
    analysis = analyzer.analyze_meeting(TEST_TRANSCRIPTS["technical"], empty_metadata)
    print(f"Empty metadata → {analysis.meeting_type.value} (confidence: {analysis.confidence:.2f})")
    
    # Test with mixed signals
    mixed_transcript = """
    Yesterday I worked on the architecture review. Today I need career feedback 
    on my performance review. We also need to coordinate the business strategy 
    for our quarterly planning standup meeting.
    """
    analysis = analyzer.analyze_meeting(mixed_transcript)
    print(f"Mixed signals → {analysis.meeting_type.value} (confidence: {analysis.confidence:.2f})")

def main():
    """Run all tests"""
    print("🚀 Universal Meeting Intelligence System - Test Suite")
    print("=" * 60)
    
    try:
        # Run all tests
        detection_results = test_meeting_type_detection()
        test_adaptive_prompts()
        test_booking_context_detection()
        test_edge_cases()
        
        print("\n✅ All tests completed successfully!")
        
        # Summary
        correct_detections = sum(1 for r in detection_results.values() if r['correct'])
        total_detections = len(detection_results)
        
        print(f"\n📈 Summary:")
        print(f"  Meeting Type Detection: {correct_detections}/{total_detections}")
        print(f"  System Status: {'🟢 Ready for Integration' if correct_detections >= 4 else '🟡 Needs Tuning'}")
        
        if correct_detections < 4:
            print("\n💡 Recommendations:")
            for meeting_type, result in detection_results.items():
                if not result['correct']:
                    print(f"  - Improve {meeting_type} detection (detected as {result['detected']})")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 