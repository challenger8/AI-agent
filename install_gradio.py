#!/usr/bin/env python3
"""
Install script for Gradio MCP Client
"""
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing Gradio MCP Client requirements...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "gradio>=4.0.0", 
            "pandas>=1.5.0", 
            "plotly>=5.0.0",
            "python-dotenv>=1.0.0"
        ])
        print("✅ All requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

if __name__ == "__main__":
    success = install_requirements()
    if success:
        print("\n🚀 Ready to run!")
        print("Run: python launch_gradio.py")
    else:
        print("\n❌ Installation failed. Please install manually:")
        print("pip install gradio pandas plotly python-dotenv")
