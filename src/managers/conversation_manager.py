"""
Conversation Manager for tracking and managing conversation history
Enables context-aware responses in the Voxtral model
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

# Setup logging
conversation_logger = logging.getLogger("conversation_manager")
conversation_logger.setLevel(logging.DEBUG)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages conversation history and context for context-aware responses
    
    Features:
    - Tracks conversation history with timestamps
    - Provides context window for LLM prompts
    - Maintains configurable history size
    - Exports conversation as JSON
    """
    
    def __init__(self, context_window: int = 5, max_history: int = 100):
        """
        Initialize ConversationManager
        
        Args:
            context_window: Number of recent turns to include in context (default: 5)
            max_history: Maximum number of turns to keep in history (default: 100)
        """
        self.history: List[ConversationTurn] = []
        self.context_window = context_window
        self.max_history = max_history
        
        conversation_logger.info(
            f"📝 ConversationManager initialized (context_window={context_window}, max_history={max_history})"
        )
    
    def add_turn(self, role: str, content: str, latency_ms: Optional[int] = None, 
                 metadata: Optional[Dict] = None) -> None:
        """
        Add a turn to conversation history
        
        Args:
            role: "user" or "assistant"
            content: The message content
            latency_ms: Optional latency in milliseconds
            metadata: Optional metadata dictionary
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
        self.history.append(turn)
        
        # Keep history size under limit
        if len(self.history) > self.max_history:
            removed_turn = self.history.pop(0)
            conversation_logger.debug(
                f"📝 Removed oldest turn (history size: {len(self.history)}/{self.max_history})"
            )
        
        conversation_logger.debug(
            f"📝 Added {role} turn: '{content[:50]}...' (history size: {len(self.history)})"
        )
    
    def get_context(self, num_turns: Optional[int] = None) -> str:
        """
        Get conversation context for LLM prompt
        
        Args:
            num_turns: Number of recent turns to include (default: context_window)
        
        Returns:
            Formatted conversation context string
        """
        num_turns = num_turns or self.context_window
        recent_turns = self.history[-num_turns:]
        
        context = ""
        for turn in recent_turns:
            context += f"{turn.role.upper()}: {turn.content}\n"
        
        conversation_logger.debug(
            f"📝 Generated context with {len(recent_turns)} turns ({len(context)} chars)"
        )
        
        return context
    
    def get_last_user_message(self) -> Optional[str]:
        """
        Get the last user message from history
        
        Returns:
            Last user message or None if no user messages exist
        """
        for turn in reversed(self.history):
            if turn.role == "user":
                return turn.content
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the last assistant message from history
        
        Returns:
            Last assistant message or None if no assistant messages exist
        """
        for turn in reversed(self.history):
            if turn.role == "assistant":
                return turn.content
        return None
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about conversation history
        
        Returns:
            Dictionary with history statistics
        """
        user_turns = sum(1 for turn in self.history if turn.role == "user")
        assistant_turns = sum(1 for turn in self.history if turn.role == "assistant")
        total_chars = sum(len(turn.content) for turn in self.history)
        avg_latency = None
        
        latencies = [turn.latency_ms for turn in self.history if turn.latency_ms is not None]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
        
        return {
            "total_turns": len(self.history),
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "total_characters": total_chars,
            "average_latency_ms": avg_latency,
            "context_window": self.context_window,
            "max_history": self.max_history
        }
    
    def clear_history(self) -> None:
        """Clear all conversation history"""
        self.history.clear()
        conversation_logger.info("📝 Conversation history cleared")
    
    def export_conversation(self) -> Dict[str, Any]:
        """
        Export conversation as JSON-serializable dictionary
        
        Returns:
            Dictionary containing conversation turns and metadata
        """
        return {
            "turns": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp.isoformat(),
                    "latency_ms": turn.latency_ms,
                    "metadata": turn.metadata
                }
                for turn in self.history
            ],
            "total_turns": len(self.history),
            "summary": self.get_history_summary()
        }
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export conversation to JSON file
        
        Args:
            filepath: Path to save JSON file
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.export_conversation(), f, indent=2)
            conversation_logger.info(f"📝 Conversation exported to {filepath}")
        except Exception as e:
            conversation_logger.error(f"❌ Failed to export conversation: {e}")
    
    def __len__(self) -> int:
        """Return number of turns in history"""
        return len(self.history)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ConversationManager(turns={len(self.history)}, context_window={self.context_window})"

