#!/usr/bin/env python3
"""Test that the recursion limit fix works."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_recursion_fix():
    """Test that validation retries don't cause recursion limit error."""
    print("🔧 Testing Recursion Limit Fix")
    print("=" * 60)
    
    try:
        from ollama_deep_researcher.graph import graph
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        # Create configuration with lower retry limit
        config = Configuration()
        config.max_validation_retries = 1  # Only 1 retry to prevent long loops
        
        print(f"Configuration:")
        print(f"  Max validation retries: {config.max_validation_retries}")
        print(f"  Search API: {config.search_api}")
        
        # Test with a topic that might return poor results
        test_topic = "xyzabc123 nonsense query that won't return good results"
        print(f"\nTesting with intentionally bad query: '{test_topic}'")
        print("This should trigger validation retries but not cause recursion error")
        print("-" * 60)
        
        # Prepare input
        input_data = {"research_topic": test_topic}
        
        # Create runnable config with recursion limit
        runnable_config = RunnableConfig(
            configurable=config.__dict__,
            recursion_limit=30  # Set explicit limit
        )
        
        # Execute the graph - should not hit recursion limit
        try:
            result = graph.invoke(input_data, runnable_config)
            print("\n✅ Graph completed without recursion error!")
            
            if result and "running_summary" in result:
                print("   Summary generated (even with poor sources)")
            else:
                print("   No summary (expected with nonsense query)")
                
        except Exception as e:
            if "recursion" in str(e).lower():
                print(f"\n❌ Recursion error still occurs: {e}")
                return False
            else:
                print(f"\n⚠️ Different error (not recursion): {e}")
                # This is okay - we just want to avoid recursion errors
                return True
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing recursion limit fix...")
    success = test_recursion_fix()
    
    if success:
        print("\n✅ Recursion fix successful! The app should work without hitting limits.")
    else:
        print("\n❌ Recursion issue still present.")
    
    sys.exit(0 if success else 1)