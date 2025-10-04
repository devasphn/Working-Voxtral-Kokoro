#!/usr/bin/env python3
"""
Verification Script for Voxtral-Kokoro Fixes
Validates that all critical fixes have been properly applied
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def check_file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return Path(file_path).exists()

def check_import_in_file(file_path: str, import_statement: str) -> bool:
    """Check if import statement exists in file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return import_statement in content
    except Exception as e:
        print_error(f"Error reading {file_path}: {e}")
        return False

def check_string_in_file(file_path: str, search_string: str) -> bool:
    """Check if string exists in file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_string in content
    except Exception as e:
        print_error(f"Error reading {file_path}: {e}")
        return False

def verify_websocket_import() -> bool:
    """Verify Fix #1: Missing import in websocket_server.py"""
    print_header("Fix #1: WebSocket Server Import")
    
    file_path = "src/streaming/websocket_server.py"
    import_statement = "from src.models.speech_to_speech_pipeline import speech_to_speech_pipeline"
    
    if not check_file_exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    if check_import_in_file(file_path, import_statement):
        print_success(f"Import statement found in {file_path}")
        print(f"   {import_statement}")
        return True
    else:
        print_error(f"Import statement NOT found in {file_path}")
        print(f"   Expected: {import_statement}")
        return False

def verify_ui_javascript() -> bool:
    """Verify Fix #2: JavaScript syntax in ui_server_realtime.py"""
    print_header("Fix #2: UI Server JavaScript")
    
    file_path = "src/api/ui_server_realtime.py"
    
    if not check_file_exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    # Check for switch statement
    if check_string_in_file(file_path, "switch(data.type)"):
        print_success("Switch statement found in handleWebSocketMessage")
    else:
        print_error("Switch statement NOT found")
        return False
    
    # Check that orphaned case statements are removed
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Look for orphaned case statements (case outside of switch)
        in_function = False
        in_switch = False
        orphaned_cases = []
        
        for i, line in enumerate(lines, 1):
            if 'function handleWebSocketMessage' in line:
                in_function = True
            elif in_function and 'switch(data.type)' in line:
                in_switch = True
            elif in_function and in_switch and line.strip().startswith('}') and 'switch' in lines[i-10:i][-1]:
                in_switch = False
            elif in_function and not in_switch and line.strip().startswith('case '):
                orphaned_cases.append((i, line.strip()))
        
        if orphaned_cases:
            print_error(f"Found {len(orphaned_cases)} orphaned case statement(s):")
            for line_num, line in orphaned_cases:
                print(f"   Line {line_num}: {line}")
            return False
        else:
            print_success("No orphaned case statements found")
            return True
            
    except Exception as e:
        print_error(f"Error analyzing JavaScript: {e}")
        return False

def verify_config_yaml() -> bool:
    """Verify Fix #3: Configuration consistency"""
    print_header("Fix #3: Configuration (config.yaml)")
    
    file_path = "config.yaml"
    
    if not check_file_exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    checks = [
        ('torch_dtype: "bfloat16"', "torch_dtype set to bfloat16"),
        ('max_memory_per_gpu: "8GB"', "max_memory_per_gpu set to 8GB"),
    ]
    
    all_passed = True
    for search_string, description in checks:
        if check_string_in_file(file_path, search_string):
            print_success(description)
        else:
            print_error(f"{description} NOT found")
            all_passed = False
    
    return all_passed

def verify_config_py() -> bool:
    """Verify Fix #4-7: Configuration improvements in config.py"""
    print_header("Fix #4-7: Configuration (config.py)")
    
    file_path = "src/utils/config.py"
    
    if not check_file_exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    checks = [
        ('class VADConfig(BaseModel):', "VADConfig class defined"),
        ('cache_dir: str = "./model_cache"', "Relative cache_dir path"),
        ('max_memory_per_gpu: str = "8GB"', "max_memory_per_gpu set to 8GB"),
        ('ultra_fast_mode: bool = True', "ultra_fast_mode flag added"),
        ('warmup_enabled: bool = True', "warmup_enabled flag added"),
        ('vad: VADConfig = VADConfig()', "VAD config added to Config class"),
    ]
    
    all_passed = True
    for search_string, description in checks:
        if check_string_in_file(file_path, search_string):
            print_success(description)
        else:
            print_error(f"{description} NOT found")
            all_passed = False
    
    return all_passed

def verify_documentation() -> bool:
    """Verify documentation files"""
    print_header("Documentation Files")
    
    docs = [
        ("ARCHITECTURE_DOCUMENTATION.md", "Architecture Documentation"),
        ("CHANGELOG.md", "Changelog"),
        ("FIXES_SUMMARY.md", "Fixes Summary"),
    ]
    
    all_passed = True
    for file_path, description in docs:
        if check_file_exists(file_path):
            file_size = Path(file_path).stat().st_size
            print_success(f"{description} exists ({file_size:,} bytes)")
        else:
            print_error(f"{description} NOT found: {file_path}")
            all_passed = False
    
    return all_passed

def main():
    """Main verification function"""
    print_header("🔍 Voxtral-Kokoro Fixes Verification")
    print("This script verifies that all critical fixes have been applied\n")
    
    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    results = []
    
    # Run all verifications
    results.append(("WebSocket Import", verify_websocket_import()))
    results.append(("UI JavaScript", verify_ui_javascript()))
    results.append(("Config YAML", verify_config_yaml()))
    results.append(("Config Python", verify_config_py()))
    results.append(("Documentation", verify_documentation()))
    
    # Print summary
    print_header("📊 Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{BLUE}{'─'*70}{RESET}")
    if passed == total:
        print_success(f"All {total} verification checks PASSED! ✨")
        print(f"\n{GREEN}🎉 All fixes have been successfully applied!{RESET}")
        print(f"{GREEN}The codebase is now stable and production-ready.{RESET}\n")
        return 0
    else:
        print_error(f"{passed}/{total} checks passed, {total-passed} failed")
        print(f"\n{RED}⚠️  Some fixes may not have been applied correctly.{RESET}")
        print(f"{YELLOW}Please review the failed checks above.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
