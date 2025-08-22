#!/usr/bin/env python3
"""Debug environment variable issues in Flask threading."""

import os
import threading
from dotenv import load_dotenv

def test_main_thread():
    """Test environment in main thread."""
    print("=== MAIN THREAD ===")
    load_dotenv()
    
    print(f"TAVILY_API_KEY: {bool(os.getenv('TAVILY_API_KEY'))}")
    print(f"LOCAL_LLM: {os.getenv('LOCAL_LLM', 'NOT_SET')}")
    
    if os.getenv('TAVILY_API_KEY'):
        print(f"Tavily key: {os.getenv('TAVILY_API_KEY')[:15]}...")

def test_background_thread():
    """Test environment in background thread."""
    print("\n=== BACKGROUND THREAD (before load_dotenv) ===")
    print(f"TAVILY_API_KEY: {bool(os.getenv('TAVILY_API_KEY'))}")
    print(f"LOCAL_LLM: {os.getenv('LOCAL_LLM', 'NOT_SET')}")
    
    print("\n=== BACKGROUND THREAD (after load_dotenv) ===")
    load_dotenv()
    print(f"TAVILY_API_KEY: {bool(os.getenv('TAVILY_API_KEY'))}")
    print(f"LOCAL_LLM: {os.getenv('LOCAL_LLM', 'NOT_SET')}")
    
    if os.getenv('TAVILY_API_KEY'):
        print(f"Tavily key: {os.getenv('TAVILY_API_KEY')[:15]}...")
        
        # Test actual Tavily call
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
            result = client.search('test', max_results=1)
            print(f"✅ Tavily works in background thread")
        except Exception as e:
            print(f"❌ Tavily failed in background thread: {e}")

def test_explicit_env_passing(env_vars):
    """Test explicit environment variable passing."""
    print("\n=== BACKGROUND THREAD (explicit env) ===")
    
    # Set passed environment variables
    for key, value in env_vars.items():
        if value:
            os.environ[key] = value
            print(f"Set {key}: {bool(value)}")
    
    # Test Tavily
    tavily_key = os.getenv('TAVILY_API_KEY')
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            result = client.search('test', max_results=1)
            print(f"✅ Tavily works with explicit env passing")
        except Exception as e:
            print(f"❌ Tavily failed with explicit env: {e}")
    else:
        print(f"❌ No TAVILY_API_KEY after explicit setting")

if __name__ == "__main__":
    print("🔬 ENVIRONMENT DEBUGGING")
    print("=" * 50)
    
    # Test main thread
    test_main_thread()
    
    # Test background thread
    thread = threading.Thread(target=test_background_thread)
    thread.start()
    thread.join()
    
    # Test explicit environment passing
    env_vars = {
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'LOCAL_LLM': os.getenv('LOCAL_LLM'),
    }
    
    thread2 = threading.Thread(target=test_explicit_env_passing, args=(env_vars,))
    thread2.start()
    thread2.join()