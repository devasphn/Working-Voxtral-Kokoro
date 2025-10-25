#!/usr/bin/env python3
"""
Phase 1 Testing Script: Conversation Manager
Tests conversation history tracking and context-aware responses
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE1_TEST")

# Import the conversation manager
from src.managers.conversation_manager import ConversationManager


def test_conversation_manager_basic():
    """Test basic ConversationManager functionality"""
    
    logger.info("=" * 80)
    logger.info("PHASE 1 TEST: Conversation Manager - Basic Functionality")
    logger.info("=" * 80)
    
    try:
        # Initialize conversation manager
        logger.info("\n[TEST 1] Initialize ConversationManager...")
        cm = ConversationManager(context_window=5, max_history=100)
        logger.info(f"✅ ConversationManager initialized: {cm}")
        
        # Test adding turns
        logger.info("\n[TEST 2] Add conversation turns...")
        cm.add_turn("user", "Hello, how are you?")
        cm.add_turn("assistant", "I'm doing great, thanks for asking!")
        cm.add_turn("user", "What's the weather like?")
        cm.add_turn("assistant", "I don't have access to real-time weather data, but you can check a weather service.")
        logger.info(f"✅ Added 4 turns to conversation")
        
        # Test history length
        logger.info("\n[TEST 3] Check history length...")
        assert len(cm) == 4, f"Expected 4 turns, got {len(cm)}"
        logger.info(f"✅ History length correct: {len(cm)} turns")
        
        # Test get_context
        logger.info("\n[TEST 4] Get conversation context...")
        context = cm.get_context()
        logger.info(f"✅ Context retrieved ({len(context)} chars):")
        logger.info(f"   {context[:100]}...")
        
        # Verify context format
        assert "USER:" in context, "Context should contain USER role"
        assert "ASSISTANT:" in context, "Context should contain ASSISTANT role"
        logger.info(f"✅ Context format correct")
        
        # Test get_last_user_message
        logger.info("\n[TEST 5] Get last user message...")
        last_user = cm.get_last_user_message()
        assert last_user == "What's the weather like?", f"Expected last user message, got: {last_user}"
        logger.info(f"✅ Last user message: '{last_user}'")
        
        # Test get_last_assistant_message
        logger.info("\n[TEST 6] Get last assistant message...")
        last_assistant = cm.get_last_assistant_message()
        assert "weather" in last_assistant.lower(), f"Expected weather response, got: {last_assistant}"
        logger.info(f"✅ Last assistant message: '{last_assistant[:50]}...'")
        
        # Test history summary
        logger.info("\n[TEST 7] Get history summary...")
        summary = cm.get_history_summary()
        logger.info(f"✅ History summary:")
        logger.info(f"   Total turns: {summary['total_turns']}")
        logger.info(f"   User turns: {summary['user_turns']}")
        logger.info(f"   Assistant turns: {summary['assistant_turns']}")
        logger.info(f"   Total characters: {summary['total_characters']}")
        
        assert summary['total_turns'] == 4, "Expected 4 total turns"
        assert summary['user_turns'] == 2, "Expected 2 user turns"
        assert summary['assistant_turns'] == 2, "Expected 2 assistant turns"
        logger.info(f"✅ Summary statistics correct")
        
        # Test export
        logger.info("\n[TEST 8] Export conversation...")
        export = cm.export_conversation()
        assert "turns" in export, "Export should contain 'turns' key"
        assert len(export["turns"]) == 4, "Export should have 4 turns"
        logger.info(f"✅ Conversation exported successfully")
        
        # Test context window
        logger.info("\n[TEST 9] Test context window...")
        context_3 = cm.get_context(num_turns=3)
        context_2 = cm.get_context(num_turns=2)
        assert len(context_3) > len(context_2), "Larger context window should have more content"
        logger.info(f"✅ Context window working correctly")
        logger.info(f"   3 turns: {len(context_3)} chars")
        logger.info(f"   2 turns: {len(context_2)} chars")
        
        # Test clear history
        logger.info("\n[TEST 10] Clear history...")
        cm.clear_history()
        assert len(cm) == 0, "History should be empty after clear"
        logger.info(f"✅ History cleared successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_conversation_manager_with_latency():
    """Test ConversationManager with latency tracking"""
    
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 TEST: Conversation Manager - Latency Tracking")
    logger.info("=" * 80)
    
    try:
        cm = ConversationManager(context_window=3, max_history=50)
        
        logger.info("\n[TEST 1] Add turns with latency...")
        cm.add_turn("user", "First question", latency_ms=100)
        cm.add_turn("assistant", "First response", latency_ms=250)
        cm.add_turn("user", "Second question", latency_ms=80)
        cm.add_turn("assistant", "Second response", latency_ms=300)
        logger.info(f"✅ Added 4 turns with latency tracking")
        
        logger.info("\n[TEST 2] Check latency in summary...")
        summary = cm.get_history_summary()
        assert summary['average_latency_ms'] is not None, "Average latency should be calculated"
        logger.info(f"✅ Average latency: {summary['average_latency_ms']:.1f}ms")
        
        logger.info("\n[TEST 3] Export with latency...")
        export = cm.export_conversation()
        for i, turn in enumerate(export["turns"]):
            if turn['latency_ms']:
                logger.info(f"   Turn {i}: {turn['role']} - {turn['latency_ms']}ms")
        logger.info(f"✅ Latency exported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_conversation_manager_max_history():
    """Test ConversationManager max history limit"""
    
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 TEST: Conversation Manager - Max History Limit")
    logger.info("=" * 80)
    
    try:
        cm = ConversationManager(context_window=5, max_history=10)
        
        logger.info("\n[TEST 1] Add turns beyond max_history...")
        for i in range(15):
            cm.add_turn("user", f"Question {i}")
            cm.add_turn("assistant", f"Response {i}")
        
        logger.info(f"✅ Added 30 turns (15 pairs)")
        
        logger.info("\n[TEST 2] Check history size...")
        assert len(cm) == 10, f"Expected max 10 turns, got {len(cm)}"
        logger.info(f"✅ History size limited to {len(cm)} turns (max_history=10)")
        
        logger.info("\n[TEST 3] Verify oldest turns were removed...")
        last_user = cm.get_last_user_message()
        assert "Question 14" in last_user, f"Expected latest question, got: {last_user}"
        logger.info(f"✅ Latest turn is correct: '{last_user}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all Phase 1 tests"""
    
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 COMPREHENSIVE TEST SUITE")
    logger.info("=" * 80)
    
    results = {}
    
    # Test 1: Basic functionality
    logger.info("\n[TEST SUITE 1/3] Basic Functionality")
    results['basic'] = test_conversation_manager_basic()
    
    # Test 2: Latency tracking
    logger.info("\n[TEST SUITE 2/3] Latency Tracking")
    results['latency'] = test_conversation_manager_with_latency()
    
    # Test 3: Max history limit
    logger.info("\n[TEST SUITE 3/3] Max History Limit")
    results['max_history'] = test_conversation_manager_max_history()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ ALL PHASE 1 TESTS PASSED")
        logger.info("ConversationManager is working correctly!")
        logger.info("\nKey features verified:")
        logger.info("  ✅ Conversation history tracking")
        logger.info("  ✅ Context window management")
        logger.info("  ✅ Latency tracking")
        logger.info("  ✅ History size limits")
        logger.info("  ✅ Export functionality")
        return 0
    else:
        logger.error("\n❌ SOME PHASE 1 TESTS FAILED")
        logger.error("Please review the errors above")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

