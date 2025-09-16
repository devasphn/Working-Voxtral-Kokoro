#!/usr/bin/env python3
"""
Dependency Installation Script
Installs all required packages for Voxtral + Orpheus TTS system
"""

import subprocess
import sys
import os
import platform

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n{step_num}. {title}")
    print("-" * 40)

def print_success(message):
    """Print success message"""
    print(f"   ✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"   ❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"   ⚠️ {message}")

def print_info(message):
    """Print info message"""
    print(f"   💡 {message}")

def run_command(command, description=""):
    """Run a command and return success status"""
    try:
        print_info(f"Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    print_step(1, "Python Version Check")
    
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print_success("Python version is compatible")
        return True
    else:
        print_error("Python 3.8+ required")
        return False

def upgrade_pip():
    """Upgrade pip to latest version"""
    print_step(2, "Upgrading pip")
    
    success = run_command(f"{sys.executable} -m pip install --upgrade pip setuptools wheel")
    if success:
        print_success("pip upgraded successfully")
    else:
        print_error("Failed to upgrade pip")
    return success

def install_pytorch():
    """Install PyTorch with appropriate backend"""
    print_step(3, "Installing PyTorch")
    
    # Check if CUDA is available
    try:
        import torch
        if torch.cuda.is_available():
            print_info("CUDA already available, skipping PyTorch installation")
            return True
    except ImportError:
        pass
    
    # Install PyTorch with CUDA support
    if platform.system() == "Windows":
        command = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    else:
        command = f"{sys.executable} -m pip install torch torchvision torchaudio"
    
    success = run_command(command)
    if success:
        print_success("PyTorch installed successfully")
    else:
        print_error("Failed to install PyTorch")
    return success

def install_transformers():
    """Install latest transformers with Voxtral support"""
    print_step(4, "Installing Transformers (Latest)")
    
    # Install latest transformers from source for Voxtral support
    command = f"{sys.executable} -m pip install git+https://github.com/huggingface/transformers.git"
    success = run_command(command)
    
    if not success:
        # Fallback to latest stable
        print_warning("Installing from source failed, trying latest stable")
        command = f"{sys.executable} -m pip install transformers>=4.56.0"
        success = run_command(command)
    
    if success:
        print_success("Transformers installed successfully")
    else:
        print_error("Failed to install Transformers")
    return success

def install_mistral_common():
    """Install mistral-common with audio support"""
    print_step(5, "Installing Mistral Common")
    
    command = f"{sys.executable} -m pip install 'mistral-common[audio]>=1.4.0'"
    success = run_command(command)
    
    if success:
        print_success("Mistral Common installed successfully")
    else:
        print_error("Failed to install Mistral Common")
    return success

def install_orpheus_tts():
    """Install Orpheus TTS"""
    print_step(6, "Installing Orpheus TTS")
    
    # Install vllm first
    command = f"{sys.executable} -m pip install 'vllm>=0.7.3,<0.8.0'"
    success = run_command(command)
    
    if not success:
        print_warning("vllm installation failed, trying without version constraints")
        command = f"{sys.executable} -m pip install vllm"
        success = run_command(command)
    
    if success:
        # Install orpheus-speech
        command = f"{sys.executable} -m pip install orpheus-speech"
        success = run_command(command)
        
        if success:
            print_success("Orpheus TTS installed successfully")
        else:
            print_error("Failed to install orpheus-speech")
    else:
        print_error("Failed to install vllm (required for Orpheus TTS)")
    
    return success

def install_web_framework():
    """Install web framework packages"""
    print_step(7, "Installing Web Framework")
    
    packages = [
        "fastapi>=0.104.0",
        "'uvicorn[standard]>=0.24.0'",
        "websockets>=12.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "httpx>=0.25.0"
    ]
    
    for package in packages:
        command = f"{sys.executable} -m pip install {package}"
        success = run_command(command)
        if not success:
            print_warning(f"Failed to install {package}, continuing...")
    
    print_success("Web framework packages installation completed")
    return True

def install_audio_packages():
    """Install audio processing packages"""
    print_step(8, "Installing Audio Processing")
    
    packages = [
        "librosa>=0.10.1",
        "soundfile>=0.12.1",
        "numpy>=1.24.0",
        "scipy>=1.11.0"
    ]
    
    for package in packages:
        command = f"{sys.executable} -m pip install {package}"
        success = run_command(command)
        if not success:
            print_warning(f"Failed to install {package}, continuing...")
    
    print_success("Audio processing packages installation completed")
    return True

def install_utility_packages():
    """Install utility packages"""
    print_step(9, "Installing Utility Packages")
    
    packages = [
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0",
        "huggingface-hub>=0.19.0",
        "accelerate>=0.25.0",
        "tokenizers>=0.15.0"
    ]
    
    for package in packages:
        command = f"{sys.executable} -m pip install {package}"
        success = run_command(command)
        if not success:
            print_warning(f"Failed to install {package}, continuing...")
    
    print_success("Utility packages installation completed")
    return True

def install_testing_packages():
    """Install testing packages"""
    print_step(10, "Installing Testing Packages")
    
    packages = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0"
    ]
    
    for package in packages:
        command = f"{sys.executable} -m pip install {package}"
        success = run_command(command)
        if not success:
            print_warning(f"Failed to install {package}, continuing...")
    
    print_success("Testing packages installation completed")
    return True

def verify_installation():
    """Verify that all packages are installed correctly"""
    print_step(11, "Verifying Installation")
    
    critical_packages = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("mistral_common", "Mistral Common"),
        ("fastapi", "FastAPI"),
        ("librosa", "Librosa"),
        ("numpy", "NumPy")
    ]
    
    success_count = 0
    for package, name in critical_packages:
        try:
            __import__(package)
            print_success(f"{name} imported successfully")
            success_count += 1
        except ImportError as e:
            print_error(f"{name} import failed: {e}")
    
    # Try to import Voxtral specifically
    try:
        from transformers import VoxtralForConditionalGeneration
        print_success("VoxtralForConditionalGeneration imported successfully")
        success_count += 1
    except ImportError as e:
        print_error(f"VoxtralForConditionalGeneration import failed: {e}")
        print_warning("You may need to install transformers from source")
    
    # Try optional packages
    optional_packages = [
        ("orpheus_tts", "Orpheus TTS"),
        ("vllm", "vLLM"),
        ("pydantic_settings", "Pydantic Settings")
    ]
    
    for package, name in optional_packages:
        try:
            __import__(package)
            print_success(f"{name} imported successfully")
        except ImportError as e:
            print_warning(f"{name} not available: {e}")
    
    if success_count >= len(critical_packages):
        print_success("🎉 Core installation verification passed!")
        return True
    else:
        print_error(f"❌ Only {success_count}/{len(critical_packages)} critical packages verified")
        return False

def main():
    """Main installation process"""
    print_header("Voxtral + Orpheus TTS Dependency Installation")
    
    print("This script will install all required dependencies for the")
    print("Voxtral + Orpheus TTS real-time voice agent system.")
    print("")
    
    # Check if we should proceed
    response = input("Do you want to proceed with installation? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Installation cancelled.")
        return False
    
    steps = [
        check_python_version,
        upgrade_pip,
        install_pytorch,
        install_transformers,
        install_mistral_common,
        install_orpheus_tts,
        install_web_framework,
        install_audio_packages,
        install_utility_packages,
        install_testing_packages,
        verify_installation
    ]
    
    failed_steps = []
    for i, step in enumerate(steps, 1):
        try:
            success = step()
            if not success:
                failed_steps.append(step.__name__)
        except Exception as e:
            print_error(f"Step {i} failed with exception: {e}")
            failed_steps.append(step.__name__)
    
    print_header("Installation Summary")
    
    if not failed_steps:
        print_success("🎉 All installation steps completed successfully!")
        print_info("Next steps:")
        print_info("1. Run: python validate_complete_system.py")
        print_info("2. If validation passes, start the system with: python -m src.api.ui_server_realtime")
        return True
    else:
        print_error(f"❌ {len(failed_steps)} steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print_info("You may need to install some packages manually")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
