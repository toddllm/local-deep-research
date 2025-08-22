#!/usr/bin/env python3
"""Debug the exact error message."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

def test_error_message():
    """Test the exact error message."""
    print("=== TESTING EXACT ERROR MESSAGE ===")
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        try:
            config = Configuration.from_runnable_config(RunnableConfig(configurable={}))
            print(f"❌ Should have failed but got: {config.local_llm}")
        except ValueError as e:
            error_str = str(e)
            print(f"✅ ValueError caught: '{error_str}'")
            
            if 'placeholder' in error_str:
                print(f"✅ Contains 'placeholder'")
            else:
                print(f"❌ Does NOT contain 'placeholder'")
                print(f"Looking for: 'placeholder'")
                print(f"In string: '{error_str}'")
                print(f"Lowercase: '{error_str.lower()}'")
                
                if 'placeholder' in error_str.lower():
                    print(f"✅ Contains 'placeholder' in lowercase")
                else:
                    print(f"❌ Does NOT contain 'placeholder' even in lowercase")
                    
            return True
        except Exception as e:
            print(f"❌ Unexpected exception: {type(e).__name__}: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("🔬 ERROR MESSAGE DEBUGGING")
    print("=" * 50)
    
    test_error_message()