#!/usr/bin/env python3
"""
Phase 0 Testing Script: Token Batching Fix
Tests TTFT (Time to First Token) improvement from 300-500ms to 50-100ms
"""

import asyncio
import time
import numpy as np
import torch
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE0_TEST")

# Import the model
from src.models.voxtral_model_realtime import VoxtralModel
from src.utils.config import config

async def test_phase0_ttft():
    """Test Phase 0: Token Batching Fix - TTFT Measurement"""
    
    logger.info("=" * 80)
    logger.info("PHASE 0 TEST: Token Batching Fix - TTFT Measurement")
    logger.info("=" * 80)
    
    try:
        # Initialize model
        logger.info("🚀 Initializing Voxtral model...")
        model = VoxtralModel()

        if not model.is_initialized:
            logger.error("❌ Model initialization failed")
            return False

        logger.info("✅ Model initialized successfully")
        
        # Create test audio (silence with some noise)
        logger.info("\n📝 Creating test audio...")
        sample_rate = config.audio.sample_rate
        duration_s = 2.0
        num_samples = int(sample_rate * duration_s)
        
        # Create audio with some content (not pure silence)
        audio_data = np.random.randn(num_samples).astype(np.float32) * 0.01
        audio_tensor = torch.from_numpy(audio_data).float()
        
        logger.info(f"✅ Test audio created: {duration_s}s @ {sample_rate}Hz")
        
        # Test streaming with TTFT measurement
        logger.info("\n🎯 Testing CHUNKED STREAMING with TTFT measurement...")
        logger.info("-" * 80)
        
        chunk_id = "test_phase0_001"
        ttft_measurements = []
        chunk_count = 0
        first_chunk_time = None
        
        start_time = time.time()
        
        async for chunk in model.process_realtime_chunk_streaming(
            audio_tensor, 
            chunk_id=chunk_id, 
            mode="conversation"
        ):
            if chunk['success'] and chunk['text'].strip():
                chunk_count += 1
                
                # Get TTFT from first chunk
                if first_chunk_time is None:
                    first_chunk_time = time.time() - start_time
                    ttft_ms = first_chunk_time * 1000
                    ttft_measurements.append(ttft_ms)
                    
                    logger.info(f"⚡ FIRST TOKEN LATENCY (TTFT): {ttft_ms:.1f}ms")
                    logger.info(f"   First chunk text: '{chunk['text']}'")
                    logger.info(f"   Chunk index: {chunk['chunk_index']}")
                    
                    # Check if TTFT is within target range
                    if ttft_ms < 100:
                        logger.info(f"   ✅ TTFT within target (<100ms)")
                    elif ttft_ms < 200:
                        logger.info(f"   ⚠️  TTFT acceptable (<200ms)")
                    else:
                        logger.warning(f"   ❌ TTFT exceeds target (>200ms)")
                
                # Log subsequent chunks
                if chunk_count <= 5:
                    logger.info(f"   Chunk {chunk_count}: '{chunk['text']}' @ {chunk['processing_time_ms']:.1f}ms")
                elif chunk_count == 6:
                    logger.info(f"   ... (more chunks)")
        
        total_time = time.time() - start_time
        
        logger.info("-" * 80)
        logger.info(f"\n📊 PHASE 0 TEST RESULTS:")
        logger.info(f"   Total chunks: {chunk_count}")
        logger.info(f"   Total time: {total_time*1000:.1f}ms")
        
        if ttft_measurements:
            logger.info(f"   TTFT: {ttft_measurements[0]:.1f}ms")
            
            # Verify TTFT improvement
            if ttft_measurements[0] < 100:
                logger.info(f"\n✅ PHASE 0 SUCCESS: TTFT is {ttft_measurements[0]:.1f}ms (target: <100ms)")
                return True
            elif ttft_measurements[0] < 200:
                logger.info(f"\n⚠️  PHASE 0 ACCEPTABLE: TTFT is {ttft_measurements[0]:.1f}ms (target: <100ms, acceptable: <200ms)")
                return True
            else:
                logger.error(f"\n❌ PHASE 0 FAILED: TTFT is {ttft_measurements[0]:.1f}ms (target: <100ms)")
                return False
        else:
            logger.error("❌ No chunks received")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

async def test_chunk_structure():
    """Test that chunk structure includes first_token_latency_ms"""
    
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 0 TEST: Chunk Structure Verification")
    logger.info("=" * 80)
    
    try:
        model = VoxtralModel()

        if not model.is_initialized:
            logger.error("❌ Model initialization failed")
            return False
        
        # Create test audio
        sample_rate = config.audio.sample_rate
        duration_s = 1.0
        num_samples = int(sample_rate * duration_s)
        audio_data = np.random.randn(num_samples).astype(np.float32) * 0.01
        audio_tensor = torch.from_numpy(audio_data).float()
        
        logger.info("🔍 Checking chunk structure...")
        
        chunk_id = "test_structure_001"
        first_chunk = None
        
        async for chunk in model.process_realtime_chunk_streaming(
            audio_tensor, 
            chunk_id=chunk_id, 
            mode="conversation"
        ):
            if chunk['success'] and chunk['text'].strip() and first_chunk is None:
                first_chunk = chunk
                break
        
        if first_chunk:
            logger.info(f"✅ First chunk received:")
            logger.info(f"   - text: '{first_chunk['text']}'")
            logger.info(f"   - is_final: {first_chunk.get('is_final')}")
            logger.info(f"   - chunk_index: {first_chunk.get('chunk_index')}")
            logger.info(f"   - processing_time_ms: {first_chunk.get('processing_time_ms'):.1f}")
            
            # Check for new field
            if 'first_token_latency_ms' in first_chunk:
                logger.info(f"   - first_token_latency_ms: {first_chunk.get('first_token_latency_ms')}ms ✅")
                return True
            else:
                logger.warning(f"   - first_token_latency_ms: NOT FOUND ⚠️")
                return False
        else:
            logger.error("❌ No chunks received")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

async def main():
    """Run all Phase 0 tests"""
    
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 0 COMPREHENSIVE TEST SUITE")
    logger.info("=" * 80)
    
    results = {}
    
    # Test 1: TTFT Measurement
    logger.info("\n[TEST 1/2] TTFT Measurement")
    results['ttft'] = await test_phase0_ttft()
    
    # Test 2: Chunk Structure
    logger.info("\n[TEST 2/2] Chunk Structure Verification")
    results['structure'] = await test_chunk_structure()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 0 TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ ALL PHASE 0 TESTS PASSED")
        logger.info("Ready to proceed to Phase 1")
        return 0
    else:
        logger.error("\n❌ SOME PHASE 0 TESTS FAILED")
        logger.error("Please review the errors above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

