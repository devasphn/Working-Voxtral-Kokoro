"""
PHASE 7: Emotion Detection Module
Detects emotions from text using keyword/pattern matching and sentiment analysis
"""

import logging
from typing import Tuple, Dict, Optional

# Setup logging
emotion_logger = logging.getLogger(__name__)

class EmotionDetector:
    """Detects emotions from text with confidence scores"""
    
    # PHASE 7: Emotion keywords for detection
    EMOTION_KEYWORDS = {
        "happy": [
            "happy", "glad", "joyful", "delighted", "wonderful", "great", "excellent",
            "fantastic", "awesome", "love", "beautiful", "perfect", "brilliant",
            "cheerful", "pleasant", "lovely", "nice", "good"
        ],
        "sad": [
            "sad", "unhappy", "depressed", "miserable", "terrible", "awful", "horrible",
            "bad", "disappointed", "upset", "down", "gloomy", "sorrowful",
            "melancholy", "lonely", "heartbroken", "devastated", "grief", "mourning"
        ],
        "angry": [
            "angry", "furious", "mad", "rage", "enraged", "livid", "irritated", "annoyed",
            "frustrated", "cross", "hostile", "aggressive", "violent", "hate",
            "despise", "disgusted", "outraged", "incensed", "seething"
        ],
        "excited": [
            "excited", "thrilled", "enthusiastic", "energetic", "pumped", "stoked",
            "ecstatic", "elated", "overjoyed", "eager", "passionate", "vibrant",
            "dynamic", "lively", "spirited", "animated", "amazing"
        ],
        "neutral": [
            "okay", "fine", "alright", "normal", "regular", "standard", "typical",
            "ordinary", "common", "usual", "average", "moderate", "calm", "peaceful"
        ]
    }
    
    # PHASE 7: Emotion intensifiers
    INTENSIFIERS = {
        "very": 1.2,
        "extremely": 1.4,
        "incredibly": 1.5,
        "absolutely": 1.3,
        "really": 1.1,
        "so": 1.1,
        "quite": 1.05,
        "rather": 1.05,
        "somewhat": 0.8,
        "slightly": 0.7,
        "a bit": 0.7,
        "a little": 0.7
    }
    
    # PHASE 7: Emotion negators
    NEGATORS = ["not", "no", "never", "neither", "nobody", "nothing", "nowhere"]
    
    def __init__(self):
        """Initialize emotion detector"""
        emotion_logger.info("🎭 [PHASE 7] Initializing EmotionDetector")
        self.supported_emotions = list(self.EMOTION_KEYWORDS.keys())
        emotion_logger.info(f"🎭 [PHASE 7] Supported emotions: {self.supported_emotions}")
    
    def detect_emotion(self, text: str) -> Tuple[str, float]:
        """
        PHASE 7: Detect emotion from text with confidence score
        
        Args:
            text: Input text to analyze
        
        Returns:
            Tuple of (emotion_label, confidence_score)
            - emotion_label: One of the supported emotions
            - confidence_score: 0.0-1.0 indicating confidence
        """
        if not text or not text.strip():
            emotion_logger.warning("⚠️ [PHASE 7] Empty text provided for emotion detection")
            return "neutral", 0.5
        
        text_lower = text.lower()
        emotion_scores = {emotion: 0.0 for emotion in self.supported_emotions}
        
        # PHASE 7: Check for negation (reverses emotion)
        has_negation = any(negator in text_lower for negator in self.NEGATORS)
        
        # PHASE 7: Score each emotion based on keyword matches
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Base score for keyword match
                    score = 1.0
                    
                    # PHASE 7: Apply intensifier multiplier
                    for intensifier, multiplier in self.INTENSIFIERS.items():
                        if intensifier in text_lower:
                            # Check if intensifier is near the keyword
                            keyword_pos = text_lower.find(keyword)
                            intensifier_pos = text_lower.find(intensifier)
                            if abs(keyword_pos - intensifier_pos) < 20:  # Within 20 chars
                                score *= multiplier
                                break
                    
                    # PHASE 7: Apply negation (reverse emotion)
                    if has_negation and emotion != "neutral":
                        score *= 0.3  # Reduce confidence if negated
                    
                    emotion_scores[emotion] += score
        
        # PHASE 7: Normalize scores
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_score
        else:
            # No keywords found, default to neutral
            emotion_scores["neutral"] = 1.0
        
        # PHASE 7: Find emotion with highest score
        detected_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[detected_emotion]
        
        # PHASE 7: Ensure minimum confidence threshold
        if confidence < 0.3:
            detected_emotion = "neutral"
            confidence = 0.5
        
        emotion_logger.debug(f"🎭 [PHASE 7] Detected emotion: {detected_emotion} (confidence: {confidence:.2f})")
        emotion_logger.debug(f"🎭 [PHASE 7] Emotion scores: {emotion_scores}")
        
        return detected_emotion, confidence
    
    def get_supported_emotions(self) -> list:
        """
        PHASE 7: Get list of supported emotions
        
        Returns:
            List of supported emotion labels
        """
        return self.supported_emotions
    
    def get_emotion_keywords(self, emotion: str) -> Optional[list]:
        """
        PHASE 7: Get keywords for a specific emotion
        
        Args:
            emotion: Emotion label
        
        Returns:
            List of keywords for the emotion, or None if emotion not supported
        """
        return self.EMOTION_KEYWORDS.get(emotion)
    
    def analyze_text(self, text: str) -> Dict:
        """
        PHASE 7: Comprehensive emotion analysis
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with detailed emotion analysis
        """
        emotion, confidence = self.detect_emotion(text)
        
        # PHASE 7: Calculate all emotion scores
        text_lower = text.lower()
        emotion_scores = {emotion: 0.0 for emotion in self.supported_emotions}
        
        for emotion_label, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[emotion_label] += 1.0
        
        # Normalize
        total = sum(emotion_scores.values())
        if total > 0:
            for emotion_label in emotion_scores:
                emotion_scores[emotion_label] /= total
        
        return {
            "detected_emotion": emotion,
            "confidence": confidence,
            "emotion_scores": emotion_scores,
            "text_length": len(text),
            "has_negation": any(neg in text_lower for neg in self.NEGATORS)
        }
    
    def get_intensity(self, text: str) -> float:
        """
        PHASE 7: Get emotion intensity (0.0-2.0)
        
        Args:
            text: Input text to analyze
        
        Returns:
            Intensity score for TTS synthesis
        """
        text_lower = text.lower()
        intensity = 1.0  # Default neutral intensity
        
        # PHASE 7: Apply intensifier multipliers
        for intensifier, multiplier in self.INTENSIFIERS.items():
            if intensifier in text_lower:
                intensity *= multiplier
        
        # PHASE 7: Clamp to valid range
        intensity = max(0.5, min(2.0, intensity))
        
        emotion_logger.debug(f"🎭 [PHASE 7] Calculated intensity: {intensity:.2f}")
        return intensity

