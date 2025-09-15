#!/usr/bin/env python3
"""
Verify Perfect Setup
Final verification that everything is correctly configured
"""

import os
import sys
from pathlib import Path

def verify_perfect_setup():
    """Verify that the perfect setup is complete and correct"""
    
    print("🔍 Verifying Perfect Setup")
    print("=" * 50)
    
    issues = []
    successes = []
    
    # Check 1: Required files exist
    required_files = [
        "requirements.txt",
        "src/tts/orpheus_perfect_model.py",
        "src/tts/tts_service_perfect.py", 
        "src/models/voxtral_model_realtime.py",
        "src/models/unified_model_manager.py",
        "src/utils/config.py",
        "config.yaml",
        "start_perfect.sh",
        "test_perfect_system.py",
        "RUNPOD_COMMANDS.md"
    ]
    
    print("1. Checking required files...")
    for file in required_files:
        if os.path.exists(file):
            successes.append(f"✅ {file}")
        else:
            issues.append(f"❌ MISSING: {file}")
    
    # Check 2: Unnecessary files removed
    unnecessary_files = [
        "deploy_direct_orpheus.sh",
        "config_direct_orpheus.yaml",
        "src/tts/orpheus_direct_model.py",
        "src/tts/tts_service_direct.py",
        "tests/test_snac_integration.py",
        "tests/test_token_processing.py",
        "FINAL_CORRECTIONS_SUMMARY.md",
        "IMPLEMENTATION_COMPLETE.md",
        "README_DIRECT_ORPHEUS.md",
        "RUNPOD_DEPLOYMENT_GUIDE.md",
        "validate_direct_orpheus_integration.py",
        "final_system_check.py",
        "optimize_performance.py",
        "setup.sh",
        "validate_setup.py"
    ]
    
    print("\n2. Checking unnecessary files removed...")
    for file in unnecessary_files:
        if not os.path.exists(file):
            successes.append(f"✅ REMOVED: {file}")
        else:
            issues.append(f"❌ STILL EXISTS: {file}")
    
    # Check 3: Requirements.txt content
    print("\n3. Checking requirements.txt content...")
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            
        if "orpheus-tts>=0.1.0" in content:
            successes.append("✅ Orpheus TTS package specified")
        else:
            issues.append("❌ Orpheus TTS package not found in requirements")
            
        if "snac" not in content or "# - snac" in content:
            successes.append("✅ SNAC package correctly excluded")
        else:
            issues.append("❌ SNAC package still included (should be excluded)")
            
        if "transformers>=4.54.0" in content:
            successes.append("✅ Transformers version correctly specified")
        else:
            issues.append("❌ Transformers version not correctly specified")
            
    except Exception as e:
        issues.append(f"❌ Could not read requirements.txt: {e}")
    
    # Check 4: Configuration files
    print("\n4. Checking configuration...")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.utils.config import config
        
        if "mistralai/Voxtral-Mini-3B-2507" in config.model.name:
            successes.append("✅ Voxtral model correctly configured")
        else:
            issues.append(f"❌ Voxtral model incorrect: {config.model.name}")
            
        if hasattr(config.tts, 'orpheus_direct') and "canopylabs/orpheus-tts-0.1-finetune-prod" in config.tts.orpheus_direct.model_name:
            successes.append("✅ Orpheus model correctly configured")
        else:
            issues.append("❌ Orpheus model not correctly configured")
            
    except Exception as e:
        issues.append(f"❌ Configuration check failed: {e}")
    
    # Check 5: Import tests
    print("\n5. Testing imports...")
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        successes.append("✅ OrpheusPerfectModel imports correctly")
    except Exception as e:
        issues.append(f"❌ OrpheusPerfectModel import failed: {e}")
    
    try:
        from src.tts.tts_service_perfect import TTSServicePerfect
        successes.append("✅ TTSServicePerfect imports correctly")
    except Exception as e:
        issues.append(f"❌ TTSServicePerfect import failed: {e}")
    
    try:
        from src.models.unified_model_manager import UnifiedModelManager
        successes.append("✅ UnifiedModelManager imports correctly")
    except Exception as e:
        issues.append(f"❌ UnifiedModelManager import failed: {e}")
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    if successes:
        print(f"\n✅ SUCCESSES ({len(successes)}):")
        for success in successes:
            print(f"  {success}")
    
    if issues:
        print(f"\n❌ ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")
    
    print(f"\n📈 SUMMARY:")
    print(f"  • Successes: {len(successes)}")
    print(f"  • Issues: {len(issues)}")
    
    if len(issues) == 0:
        print(f"\n🎉 PERFECT SETUP VERIFIED!")
        print(f"✅ All components are correctly configured")
        print(f"✅ All unnecessary files removed")
        print(f"✅ Ready for deployment on RunPod")
        print(f"\nNext step: Follow RUNPOD_COMMANDS.md")
        return True
    else:
        print(f"\n⚠️  SETUP NEEDS ATTENTION")
        print(f"❌ {len(issues)} issues need to be resolved")
        return False

if __name__ == "__main__":
    success = verify_perfect_setup()
    sys.exit(0 if success else 1)