#!/usr/bin/env python3
"""
Demo script for Abdullah Slack Clone
This script helps you run the Slack clone application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import streamlit
        import supabase
        import dotenv
        import streamlit_supabase_auth
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create .env file from dot.env.example and add your Supabase credentials")
        return False
    
    # Check if required variables are present
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        print("Please add SUPABASE_URL and SUPABASE_ANON_KEY to your .env file")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def main():
    print("🚀 Abdullah Slack Clone - Demo Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found. Make sure you're in the project directory.")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    print("\n🎯 Starting Abdullah Slack Clone...")
    print("📝 Make sure you've:")
    print("   1. Created your Supabase project")
    print("   2. Set up GitHub OAuth app") 
    print("   3. Run the schema.sql in Supabase Dashboard")
    print("   4. Configured authentication providers in Supabase")
    print("\n🌐 The app will open at http://localhost:8501")
    print("🔄 The app auto-refreshes messages every 5 seconds")
    print("\n💡 Features to try:")
    print("   • Sign in with GitHub")
    print("   • Join/create channels")
    print("   • Send messages and reactions")
    print("   • Try direct messaging")
    print("   • Create new channels")
    
    input("\nPress Enter to start the application...")
    
    try:
        # Run Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Thanks for using Abdullah Slack Clone!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
