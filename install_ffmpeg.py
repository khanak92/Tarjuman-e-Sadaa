"""
FFmpeg installation helper script for Windows
Downloads and sets up FFmpeg, adds it to system PATH
"""

import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
from pathlib import Path


def is_admin():
    """
    Check if script is running with administrator privileges
    """
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def download_ffmpeg():
    """
    Download FFmpeg from Gyan.dev (official Windows builds)
    """
    print("Downloading FFmpeg...")
    print("This may take a few minutes depending on your internet connection.")
    
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    download_path = os.path.join(os.getenv("TEMP"), "ffmpeg.zip")
    
    try:
        urllib.request.urlretrieve(ffmpeg_url, download_path)
        print(f"✅ Downloaded FFmpeg to {download_path}")
        return download_path
    except Exception as e:
        print(f"❌ Error downloading FFmpeg: {e}")
        print("\nPlease download manually from:")
        print("https://www.gyan.dev/ffmpeg/builds/")
        print("Or visit: https://ffmpeg.org/download.html")
        return None


def extract_ffmpeg(zip_path, extract_to="C:\\ffmpeg"):
    """
    Extract FFmpeg to specified directory
    
    Args:
        zip_path: Path to downloaded zip file
        extract_to: Directory to extract to
    """
    print(f"\nExtracting FFmpeg to {extract_to}...")
    
    try:
        if os.path.exists(extract_to):
            response = input(f"{extract_to} already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                extract_to = input("Enter alternative path: ").strip()
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(extract_to))
        
        extracted_folder = None
        for item in os.listdir(os.path.dirname(extract_to)):
            item_path = os.path.join(os.path.dirname(extract_to), item)
            if os.path.isdir(item_path) and 'ffmpeg' in item.lower():
                extracted_folder = item_path
                break
        
        if extracted_folder and extracted_folder != extract_to:
            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
            shutil.move(extracted_folder, extract_to)
        
        bin_path = os.path.join(extract_to, "bin")
        if os.path.exists(bin_path):
            print(f"✅ Extracted to {extract_to}")
            return bin_path
        else:
            print(f"⚠️  Extracted, but bin folder not found. Please check: {extract_to}")
            return None
            
    except Exception as e:
        print(f"❌ Error extracting FFmpeg: {e}")
        return None


def add_to_path(bin_path):
    """
    Add FFmpeg to system PATH
    
    Args:
        bin_path: Path to FFmpeg bin directory
    """
    print(f"\nAdding {bin_path} to system PATH...")
    
    if not is_admin():
        print("⚠️  Administrator privileges required to modify system PATH.")
        print("Please run this script as Administrator, or add manually:")
        print(f"   Path to add: {bin_path}")
        print("\nManual steps:")
        print("1. Press Win + X, select 'System'")
        print("2. Click 'Advanced system settings'")
        print("3. Click 'Environment Variables'")
        print("4. Under 'System variables', select 'Path' and click 'Edit'")
        print("5. Click 'New' and add the path above")
        print("6. Click 'OK' on all dialogs")
        return False
    
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            0, winreg.KEY_ALL_ACCESS
        )
        
        path_value, _ = winreg.QueryValueEx(key, "Path")
        paths = path_value.split(os.pathsep)
        
        if bin_path not in paths:
            paths.append(bin_path)
            new_path = os.pathsep.join(paths)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print("✅ Added to system PATH")
            print("⚠️  Please restart your terminal/command prompt for changes to take effect.")
            return True
        else:
            print("✅ Already in PATH")
            return True
            
    except Exception as e:
        print(f"❌ Error adding to PATH: {e}")
        return False


def verify_ffmpeg():
    """
    Verify FFmpeg installation
    """
    print("\nVerifying FFmpeg installation...")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg is working: {version_line}")
            return True
        else:
            print("❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        print("   Please restart your terminal/command prompt and try again.")
        return False
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False


def main():
    """
    Main installation process
    """
    print("=" * 60)
    print("FFmpeg Installation Helper for MSTUTS")
    print("=" * 60)
    print()
    
    if not is_admin():
        print("⚠️  WARNING: Not running as Administrator")
        print("   Some steps may require manual intervention.")
        print()
    
    choice = input("Choose installation method:\n1. Automatic download and install\n2. Manual setup (I already have FFmpeg)\nEnter choice (1/2): ")
    
    if choice == "1":
        zip_path = download_ffmpeg()
        if not zip_path:
            return
        
        extract_to = input("\nEnter installation path (default: C:\\ffmpeg): ").strip()
        if not extract_to:
            extract_to = "C:\\ffmpeg"
        
        bin_path = extract_ffmpeg(zip_path, extract_to)
        if bin_path:
            add_to_path(bin_path)
            print("\n⚠️  IMPORTANT: Restart your terminal/command prompt!")
            print("   Then run: ffmpeg -version")
    
    else:
        bin_path = input("Enter path to FFmpeg bin directory (e.g., C:\\ffmpeg\\bin): ").strip()
        if os.path.exists(bin_path) and os.path.exists(os.path.join(bin_path, "ffmpeg.exe")):
            add_to_path(bin_path)
            print("\n⚠️  IMPORTANT: Restart your terminal/command prompt!")
        else:
            print("❌ Invalid path or ffmpeg.exe not found")
    
    print("\n" + "=" * 60)
    print("After restarting terminal, run: python setup_check.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

