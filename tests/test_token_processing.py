"""
Unit tests for Orpheus token processing algorithm
Tests the correct implementation of token extraction and processing
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tts.orpheus_direct_model import OrpheusDirectModel, TokenProcessingError

class TestTokenProcessing:
    """Test suite for token processing algorithm"""
    
    def setup_method(self):
        """Setup test environment"""
        self.model = OrpheusDirectModel()
    
    def test_extract_tts_tokens_basic(self):
        """Test basic token extraction from generated text"""
        # Sample generated text with custom tokens
        generated_text = (
            "Here is some text with tokens: "
            "<custom_token_4106> <custom_token_4107> <custom_token_4108> "
            "<custom_token_4109> <custom_token_4110> <custom_token_4111> "
            "<custom_token_4112> and more text"
        )
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # Verify tokens were extracted and processed correctly
        assert len(tokens) == 7
        
        # Verify the Orpheus-FastAPI formula: token_id - 10 - ((i % 7) * 4096)
        expected_tokens = []
        raw_tokens = [4106, 4107, 4108, 4109, 4110, 4111, 4112]
        
        for i, token_id in enumerate(raw_tokens):
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_tokens.append(processed)
        
        assert tokens == expected_tokens
    
    def test_extract_tts_tokens_orpheus_formula(self):
        """Test the specific Orpheus-FastAPI token processing formula"""
        # Test with known token sequence
        generated_text = (
            "<custom_token_4106> <custom_token_8202> <custom_token_12298> "
            "<custom_token_16394> <custom_token_20490> <custom_token_24586> "
            "<custom_token_28682>"
        )
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # Calculate expected tokens using Orpheus-FastAPI formula
        raw_tokens = [4106, 8202, 12298, 16394, 20490, 24586, 28682]
        expected_tokens = []
        
        for i, token_id in enumerate(raw_tokens):
            # Formula: token_id - 10 - ((i % 7) * 4096)
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_tokens.append(processed)
        
        # Verify formula application
        # i=0: 4106 - 10 - (0 * 4096) = 4096
        # i=1: 8202 - 10 - (1 * 4096) = 4096
        # i=2: 12298 - 10 - (2 * 4096) = 4096
        # etc.
        
        assert len(tokens) == len(expected_tokens)
        assert tokens == expected_tokens
    
    def test_extract_tts_tokens_edge_cases(self):
        """Test token extraction with edge cases"""
        # Test with tokens that would result in negative values
        generated_text = (
            "<custom_token_10> <custom_token_4106> <custom_token_8202>"
        )
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # First token: 10 - 10 - (0 * 4096) = 0 (should be filtered out)
        # Second token: 4106 - 10 - (1 * 4096) = 0 (should be filtered out)  
        # Third token: 8202 - 10 - (2 * 4096) = 0 (should be filtered out)
        
        # Only positive tokens should remain
        expected_positive_tokens = []
        raw_tokens = [10, 4106, 8202]
        
        for i, token_id in enumerate(raw_tokens):
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_positive_tokens.append(processed)
        
        assert tokens == expected_positive_tokens
    
    def test_extract_tts_tokens_no_tokens(self):
        """Test token extraction when no tokens are present"""
        generated_text = "This is just regular text without any custom tokens."
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        assert tokens == []
    
    def test_extract_tts_tokens_malformed_tokens(self):
        """Test token extraction with malformed token patterns"""
        generated_text = (
            "<custom_token_abc> <custom_token_4106> <not_a_token> "
            "<custom_token_> <custom_token_4107>"
        )
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # Only valid numeric tokens should be processed
        # 4106 - 10 - (0 * 4096) = 4096
        # 4107 - 10 - (1 * 4096) = 1 (since we only count valid tokens for index)
        
        expected_tokens = []
        valid_raw_tokens = [4106, 4107]  # Only these are valid
        
        for i, token_id in enumerate(valid_raw_tokens):
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_tokens.append(processed)
        
        assert len(tokens) == len(expected_tokens)
    
    def test_extract_tts_tokens_large_sequence(self):
        """Test token extraction with a large sequence of tokens"""
        # Generate a sequence of 14 tokens (2 full cycles of 7)
        raw_token_ids = list(range(4106, 4120))  # 14 tokens
        
        generated_text = " ".join([f"<custom_token_{tid}>" for tid in raw_token_ids])
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # Calculate expected tokens
        expected_tokens = []
        for i, token_id in enumerate(raw_token_ids):
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_tokens.append(processed)
        
        assert len(tokens) == len(expected_tokens)
        assert tokens == expected_tokens
    
    def test_extract_tts_tokens_modulo_behavior(self):
        """Test the modulo behavior in the token processing formula"""
        # Test tokens at positions that demonstrate modulo 7 behavior
        raw_token_ids = [4106, 8202, 12298, 16394, 20490, 24586, 28682, 32778]  # 8 tokens
        
        generated_text = " ".join([f"<custom_token_{tid}>" for tid in raw_token_ids])
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # Verify modulo behavior
        expected_tokens = []
        for i, token_id in enumerate(raw_token_ids):
            # The key is that i % 7 cycles: 0,1,2,3,4,5,6,0,1,2...
            processed = token_id - 10 - ((i % 7) * 4096)
            if processed > 0:
                expected_tokens.append(processed)
        
        # Position 7 should have same offset as position 0
        # Position 8 should have same offset as position 1, etc.
        
        assert tokens == expected_tokens
    
    def test_token_processing_error_handling(self):
        """Test error handling in token processing"""
        # This should not raise an exception, just return empty list
        result = self.model._extract_tts_tokens("")
        assert result == []
        
        # Test with None input - should raise exception
        with pytest.raises(Exception):
            self.model._extract_tts_tokens(None)
    
    def test_token_validation_ranges(self):
        """Test that processed tokens are within expected ranges"""
        # Use tokens that should produce valid results
        generated_text = (
            "<custom_token_4106> <custom_token_8202> <custom_token_12298> "
            "<custom_token_16394> <custom_token_20490> <custom_token_24586> "
            "<custom_token_28682>"
        )
        
        tokens = self.model._extract_tts_tokens(generated_text)
        
        # All tokens should be positive integers
        for token in tokens:
            assert isinstance(token, int)
            assert token > 0
            # SNAC typically expects tokens in range 0-4096
            assert token <= 4096
    
    def test_token_sequence_consistency(self):
        """Test that token processing is consistent across multiple calls"""
        generated_text = (
            "<custom_token_4106> <custom_token_8202> <custom_token_12298>"
        )
        
        # Process the same text multiple times
        tokens1 = self.model._extract_tts_tokens(generated_text)
        tokens2 = self.model._extract_tts_tokens(generated_text)
        tokens3 = self.model._extract_tts_tokens(generated_text)
        
        # Results should be identical
        assert tokens1 == tokens2 == tokens3
        assert len(tokens1) > 0  # Should have extracted some tokens

if __name__ == "__main__":
    pytest.main([__file__])