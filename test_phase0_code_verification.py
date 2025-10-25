#!/usr/bin/env python3
"""
Phase 0 Code Verification: Verify token batching fix was applied correctly
"""

import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE0_VERIFY")

def verify_phase0_fix():
    """Verify Phase 0 token batching fix in source code"""
    
    logger.info("=" * 80)
    logger.info("PHASE 0 CODE VERIFICATION: Token Batching Fix")
    logger.info("=" * 80)
    
    # Read the file
    file_path = "src/models/voxtral_model_realtime.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        logger.info(f"\n✅ File read successfully: {file_path}")
        
        # Check 1: Verify 1-word chunk logic
        logger.info("\n[CHECK 1] Verify 1-word chunk logic...")
        
        # Look for the while loop with 1-word chunks
        pattern1 = r"while len\(word_buffer\) >= 1:"
        if re.search(pattern1, content):
            logger.info("✅ Found: while len(word_buffer) >= 1:")
            check1 = True
        else:
            logger.error("❌ NOT FOUND: while len(word_buffer) >= 1:")
            check1 = False
        
        # Check 2: Verify 1-word extraction
        logger.info("\n[CHECK 2] Verify 1-word extraction...")
        
        pattern2 = r'chunk_text = " ".join\(word_buffer\[:1\]\)'
        if re.search(pattern2, content):
            logger.info('✅ Found: chunk_text = " ".join(word_buffer[:1])')
            check2 = True
        else:
            logger.error('❌ NOT FOUND: chunk_text = " ".join(word_buffer[:1])')
            check2 = False
        
        # Check 3: Verify TTFT tracking
        logger.info("\n[CHECK 3] Verify TTFT tracking...")
        
        pattern3 = r"first_token_time = time\.time\(\) - chunk_start_time"
        if re.search(pattern3, content):
            logger.info("✅ Found: first_token_time = time.time() - chunk_start_time")
            check3 = True
        else:
            logger.error("❌ NOT FOUND: first_token_time tracking")
            check3 = False
        
        # Check 4: Verify TTFT logging
        logger.info("\n[CHECK 4] Verify TTFT logging...")
        
        pattern4 = r"\[PHASE 0\] TTFT:"
        if re.search(pattern4, content):
            logger.info("✅ Found: [PHASE 0] TTFT logging")
            check4 = True
        else:
            logger.error("❌ NOT FOUND: [PHASE 0] TTFT logging")
            check4 = False
        
        # Check 5: Verify first_token_latency_ms in yield
        logger.info("\n[CHECK 5] Verify first_token_latency_ms in yield...")
        
        pattern5 = r"'first_token_latency_ms':"
        if re.search(pattern5, content):
            logger.info("✅ Found: 'first_token_latency_ms' in yield")
            check5 = True
        else:
            logger.error("❌ NOT FOUND: 'first_token_latency_ms' in yield")
            check5 = False
        
        # Check 6: Verify OLD code is removed
        logger.info("\n[CHECK 6] Verify OLD code is removed...")
        
        # Look for the old 6-word batching logic
        pattern6_old = r"if len\(word_buffer\) >= 6:"
        if re.search(pattern6_old, content):
            logger.error("❌ FOUND OLD CODE: if len(word_buffer) >= 6:")
            logger.error("   The old 6-word batching logic should be removed!")
            check6 = False
        else:
            logger.info("✅ OLD CODE REMOVED: if len(word_buffer) >= 6:")
            check6 = True
        
        # Check 7: Verify PHASE 0 comments
        logger.info("\n[CHECK 7] Verify PHASE 0 comments...")
        
        pattern7 = r"PHASE 0 FIX"
        if re.search(pattern7, content):
            logger.info("✅ Found: PHASE 0 FIX comments")
            check7 = True
        else:
            logger.error("❌ NOT FOUND: PHASE 0 FIX comments")
            check7 = False
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        
        checks = {
            "1-word chunk logic": check1,
            "1-word extraction": check2,
            "TTFT tracking": check3,
            "TTFT logging": check4,
            "first_token_latency_ms": check5,
            "OLD code removed": check6,
            "PHASE 0 comments": check7,
        }
        
        for check_name, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{check_name}: {status}")
        
        all_passed = all(checks.values())
        
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("✅ PHASE 0 CODE VERIFICATION PASSED")
            logger.info("All required changes have been applied correctly!")
            logger.info("\nKey improvements:")
            logger.info("  • Changed from 6-word chunks to 1-word chunks")
            logger.info("  • Added TTFT (Time to First Token) tracking")
            logger.info("  • Expected TTFT: 50-100ms (vs old 300-500ms)")
            logger.info("  • Expected improvement: 3-5x faster first token")
            return 0
        else:
            logger.error("❌ PHASE 0 CODE VERIFICATION FAILED")
            logger.error("Some required changes are missing!")
            return 1
            
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return 1
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = verify_phase0_fix()
    sys.exit(exit_code)

