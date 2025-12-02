"""
Main entry point for MSTUTS application
"""

import sys
import os
import traceback

if __name__ == "__main__":
    try:
        from gui import main
        main()
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nFull error details:")
        traceback.print_exc()
        print("\nPlease make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        print("\nFull error details:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

