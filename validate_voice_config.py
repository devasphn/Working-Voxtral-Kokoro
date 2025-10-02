#!/usr/bin/env python3
"""
Voice Configuration Validation Script
Standalone script to validate voice configuration consistency across all components
"""
import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Set up logging for validation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main validation function"""
    print("🔍 Voice Configuration Validation")
    print("=" * 50)
    
    try:
        # Import validation modules
        from src.utils.voice_config_validator import voice_config_validator
        from src.utils.startup_validator import validate_startup_configuration
        
        print("📋 Running comprehensive voice configuration validation...")
        
        # 1. Run voice consistency validation
        print("\n1️⃣ Checking voice consistency across components...")
        result = voice_config_validator.validate_voice_consistency()
        
        if result.is_valid:
            print("✅ Voice configuration is consistent across all components")
        else:
            print("❌ Voice configuration inconsistencies detected")
            
            if result.voice_conflicts:
                print(f"\n🚨 Conflicts ({len(result.voice_conflicts)}):")
                for conflict in result.voice_conflicts:
                    print(f"   - {conflict}")
            
            if result.missing_configurations:
                print(f"\n⚠️ Missing Configurations ({len(result.missing_configurations)}):")
                for missing in result.missing_configurations:
                    print(f"   - {missing}")
        
        # 2. Show component voice mapping
        print(f"\n📊 Component Voice Mapping ({len(result.component_voices)} components):")
        for component, voice in sorted(result.component_voices.items()):
            status = "✅" if voice == "hf_alpha" else "❌"
            print(f"   {status} {component:40} → {voice}")
        
        # 3. Show recommendations
        if result.recommendations:
            print(f"\n💡 Recommendations ({len(result.recommendations)}):")
            for rec in result.recommendations:
                print(f"   - {rec}")
        
        # 4. Run startup validation
        print("\n2️⃣ Running startup configuration validation...")
        startup_valid = validate_startup_configuration(strict_mode=False)
        
        if startup_valid:
            print("✅ Startup configuration validation passed")
        else:
            print("❌ Startup configuration validation failed")
        
        # 5. Generate detailed report
        print("\n3️⃣ Generating detailed configuration report...")
        report = voice_config_validator.get_configuration_report()
        
        summary = report['validation_summary']
        print(f"   Total components checked: {summary['total_components_checked']}")
        print(f"   Configuration conflicts: {summary['total_conflicts']}")
        print(f"   Missing configurations: {summary['total_missing_configs']}")
        print(f"   Expected voice: {report['expected_voice']}")
        print(f"   Available voices: {len(report['available_voices'])}")
        
        # 6. Final result
        print("\n" + "=" * 50)
        if result.is_valid and startup_valid:
            print("🎉 Voice configuration validation PASSED")
            print("   All components are using consistent voice configuration")
            return True
        else:
            print("💥 Voice configuration validation FAILED")
            print("   Please fix the issues listed above")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    setup_logging()
    
    success = main()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)