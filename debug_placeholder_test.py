#!/usr/bin/env python3
"""Debug the placeholder rejection test."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

def test_placeholder_rejection():
    """Test that placeholder values are rejected."""
    print("=== TESTING PLACEHOLDER REJECTION ===")
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        print(f"Environment LOCAL_LLM: {os.getenv('LOCAL_LLM')}")
        
        # Test with empty configurable (should fall back to environment)
        print("\nTesting with empty configurable...")
        try:
            config = Configuration.from_runnable_config(RunnableConfig(configurable={}))
            print(f"❌ Unexpected success: config.local_llm = {config.local_llm}")
            print(f"Should have failed with placeholder error")
            return False
        except ValueError as e:
            print(f"✅ Correctly failed: {e}")
            if 'placeholder' in str(e):
                print(f"✅ Error mentions placeholder")
                return True
            else:
                print(f"❌ Error doesn't mention placeholder: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Import/setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_explicit_placeholder():
    """Test with explicit placeholder value."""
    print("\n=== TESTING EXPLICIT PLACEHOLDER ===")
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        print("\nTesting with explicit placeholder in config...")
        try:
            config = Configuration.from_runnable_config(
                RunnableConfig(configurable={'local_llm': 'your_model_name'})
            )
            print(f"❌ Unexpected success: config.local_llm = {config.local_llm}")
            return False
        except ValueError as e:
            print(f"✅ Correctly failed: {e}")
            return True
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔬 PLACEHOLDER REJECTION DEBUGGING")
    print("=" * 50)
    
    result1 = test_placeholder_rejection()
    result2 = test_explicit_placeholder()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Empty config test: {'✅ PASSED' if result1 else '❌ FAILED'}")
    print(f"  Explicit placeholder test: {'✅ PASSED' if result2 else '❌ FAILED'}")