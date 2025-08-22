#!/usr/bin/env python3
"""Debug the test runner logic."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

class DebugTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def assert_in(self, item, container, message=""):
        print(f"  DEBUG: assert_in('{item}', '{container}', '{message}')")
        if item not in container:
            error = f"{message}: Expected {item} in {container}"
            print(f"  DEBUG: ASSERTION FAILED: {error}")
            raise AssertionError(error)
        else:
            print(f"  DEBUG: ASSERTION PASSED")
    
    def run_test(self, test_name, test_func):
        print(f"Running {test_name}...")
        try:
            test_func()
            print(f"  ✅ PASSED")
            self.passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            self.failed += 1
            self.failures.append((test_name, str(e)))

def test_placeholder_rejection():
    """Replicate the exact test logic."""
    print("=== REPLICATING EXACT TEST LOGIC ===")
    
    runner = DebugTestRunner()
    
    def actual_test():
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        print("  DEBUG: Creating config with empty configurable")
        try:
            config = Configuration.from_runnable_config(RunnableConfig(configurable={}))
            print(f"  DEBUG: Unexpectedly succeeded with config.local_llm = {config.local_llm}")
            raise AssertionError("Should have failed with placeholder error")
        except ValueError as e:
            print(f"  DEBUG: Caught ValueError: '{e}'")
            runner.assert_in('placeholder', str(e), "Error should mention placeholder")
            print(f"  DEBUG: Test completed successfully")
    
    runner.run_test("Placeholder Rejection Debug", actual_test)
    
    return runner.passed == 1 and runner.failed == 0

if __name__ == "__main__":
    print("🔬 TEST RUNNER DEBUGGING")
    print("=" * 50)
    
    success = test_placeholder_rejection()
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")