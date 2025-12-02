"""
Setup verification script for MSTUTS
Checks if all dependencies and requirements are met
"""

import sys
import subprocess


def check_python_version():
    """
    Check if Python version is 3.8 or higher
    """
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_package(package_name, import_name=None):
    """
    Check if a package is installed
    
    Args:
        package_name: Name of the package (for pip)
        import_name: Name for import (if different from package_name)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed. Run: pip install {package_name}")
        return False


def check_ffmpeg():
    """
    Check if FFmpeg is installed and accessible
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ FFmpeg is installed and accessible")
            return True
        else:
            print("❌ FFmpeg is not working properly")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg is NOT installed or not in PATH")
        print("   Download from: https://ffmpeg.org/download.html")
        print("   Make sure to add FFmpeg to your system PATH")
        return False
    except Exception as e:
        print(f"❌ Error checking FFmpeg: {e}")
        return False


def check_cuda():
    """
    Check if CUDA is available (optional)
    """
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA is available - GPU: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("⚠️  CUDA is not available - will use CPU (slower)")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed - cannot check CUDA")
        return False


def main():
    """
    Run all checks
    """
    print("=" * 50)
    print("MSTUTS Setup Verification")
    print("=" * 50)
    print()
    
    all_ok = True
    
    print("Checking Python version...")
    if not check_python_version():
        all_ok = False
    print()
    
    print("Checking required packages...")
    packages = [
        ("torch", "torch"),
        ("openai-whisper", "whisper"),
        ("pydub", "pydub"),
        ("numpy", "numpy"),
    ]
    
    for package, import_name in packages:
        if not check_package(package, import_name):
            all_ok = False
    print()
    
    print("Checking FFmpeg...")
    if not check_ffmpeg():
        all_ok = False
    print()
    
    print("Checking CUDA (optional)...")
    check_cuda()
    print()
    
    print("=" * 50)
    if all_ok:
        print("✅ All required components are installed!")
        print("You can now run: python main.py")
    else:
        print("❌ Some components are missing.")
        print("Please install missing components and run this script again.")
    print("=" * 50)


if __name__ == "__main__":
    main()

