#!/usr/bin/env python3
"""
Test script for Abdullah Slack Clone features
Validates that all major components are working
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError:
        print("❌ Streamlit not found")
        return False
    
    try:
        from supabase import create_client
        print("✅ Supabase client imported successfully")
    except ImportError:
        print("❌ Supabase not found")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv imported successfully")
    except ImportError:
        print("❌ Python-dotenv not found")
        return False
    
    try:
        from streamlit_supabase_auth import login_form, logout_button
        print("✅ Streamlit-supabase-auth imported successfully")
    except ImportError:
        print("❌ Streamlit-supabase-auth not found")
        return False
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "app.py",
        "schema.sql", 
        "requirements.txt",
        "README.md",
        "dot.env.example",
        "run_demo.py"
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist

def test_app_structure():
    """Test that app.py has required functions"""
    print("\n🔧 Testing app structure...")
    
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_functions = [
            "init_supabase",
            "get_authenticated_supabase", 
            "create_or_update_user_profile",
            "get_user_channels",
            "get_channel_messages",
            "get_direct_messages",
            "send_message",
            "send_direct_message",
            "add_reaction",
            "remove_reaction",
            "get_message_reactions"
        ]
        
        all_found = True
        for func in required_functions:
            if f"def {func}" in content:
                print(f"✅ Function {func} found")
            else:
                print(f"❌ Function {func} missing")
                all_found = False
        
        return all_found
    
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def test_schema():
    """Test that schema.sql has required tables"""
    print("\n🗄️ Testing database schema...")
    
    try:
        with open("schema.sql", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_tables = [
            "user_profiles",
            "workspaces", 
            "channels",
            "channel_members",
            "messages",
            "message_reactions",
            "typing_indicators"
        ]
        
        all_found = True
        for table in required_tables:
            if f"CREATE TABLE IF NOT EXISTS public.{table}" in content:
                print(f"✅ Table {table} schema found")
            else:
                print(f"❌ Table {table} schema missing")
                all_found = False
        
        return all_found
    
    except Exception as e:
        print(f"❌ Error reading schema.sql: {e}")
        return False

def main():
    print("🧪 Abdullah Slack Clone - Feature Test Suite")
    print("=" * 55)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_file_structure() 
    all_tests_passed &= test_app_structure()
    all_tests_passed &= test_schema()
    
    print("\n" + "=" * 55)
    if all_tests_passed:
        print("🎉 All tests passed! Your Slack clone is ready to run.")
        print("\n🚀 Next steps:")
        print("1. Set up your .env file with Supabase credentials")
        print("2. Run the schema.sql in Supabase Dashboard")
        print("3. Configure GitHub OAuth in Supabase")
        print("4. Run: python run_demo.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("💡 Make sure you've installed all requirements:")
        print("   pip install -r requirements.txt")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
