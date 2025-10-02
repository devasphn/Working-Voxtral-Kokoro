#!/usr/bin/env python3
"""
Test Runner for Voice Configuration Validation System
Runs all voice configuration tests and generates comprehensive reports
"""
import unittest
import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def setup_test_logging():
    """Set up logging for test execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_voice_config.log')
        ]
    )

def run_voice_configuration_tests():
    """Run all voice configuration tests"""
    print("🧪 Running Voice Configuration Validation Tests")
    print("=" * 60)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    
    # Load test suites
    test_suites = []
    
    try:
        # Load unit tests
        unit_tests = loader.discover(start_dir, pattern='test_voice_configuration.py')
        test_suites.append(('Unit Tests', unit_tests))
        
        # Load integration tests
        integration_tests = loader.discover(start_dir, pattern='test_voice_integration.py')
        test_suites.append(('Integration Tests', integration_tests))
        
    except Exception as e:
        print(f"❌ Error loading tests: {e}")
        return False
    
    # Run test suites
    overall_success = True
    results = {}
    
    for suite_name, suite in test_suites:
        print(f"\n🔍 Running {suite_name}...")
        print("-" * 40)
        
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        results[suite_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        if not result.wasSuccessful():
            overall_success = False
            print(f"❌ {suite_name} failed")
        else:
            print(f"✅ {suite_name} passed")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    total_tests = sum(r['tests_run'] for r in results.values())
    total_failures = sum(r['failures'] for r in results.values())
    total_errors = sum(r['errors'] for r in results.values())
    
    for suite_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{suite_name:20} {status:8} "
              f"Tests: {result['tests_run']:3} "
              f"Failures: {result['failures']:2} "
              f"Errors: {result['errors']:2}")
    
    print("-" * 60)
    print(f"{'TOTAL':20} {'✅ PASS' if overall_success else '❌ FAIL':8} "
          f"Tests: {total_tests:3} "
          f"Failures: {total_failures:2} "
          f"Errors: {total_errors:2}")
    
    return overall_success

if __name__ == '__main__':
    setup_test_logging()
    
    success = run_voice_configuration_tests()
    
    if success:
        print("\n🎉 All voice configuration tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some voice configuration tests failed!")
        sys.exit(1)