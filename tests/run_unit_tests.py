#!/usr/bin/env python3
"""Simple test runner for unit tests - NO PYTEST DEPENDENCIES."""

import sys
import os
import traceback
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def assert_equal(self, actual, expected, message=""):
        if actual != expected:
            raise AssertionError(f"{message}: Expected {expected}, got {actual}")
    
    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(f"{message}: Expected True, got {condition}")
    
    def assert_in(self, item, container, message=""):
        if item not in container:
            raise AssertionError(f"{message}: Expected {item} in {container}")
    
    def assert_greater(self, actual, minimum, message=""):
        if actual <= minimum:
            raise AssertionError(f"{message}: Expected {actual} > {minimum}")
    
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
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST RESULTS: {self.passed}/{total} passed")
        
        if self.failed > 0:
            print(f"\nFAILURES:")
            for name, error in self.failures:
                print(f"  {name}: {error}")
            return False
        else:
            print("🎉 ALL TESTS PASSED!")
            return True

def test_configuration():
    """Test configuration system."""
    runner = TestRunner()
    
    def test_ui_model_selection_override():
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        os.environ['LOCAL_LLM'] = 'llama3.2'
        ui_config = {'local_llm': 'gpt-oss:20b'}
        runnable_config = RunnableConfig(configurable=ui_config)
        config = Configuration.from_runnable_config(runnable_config)
        
        runner.assert_equal(config.local_llm, 'gpt-oss:20b', "UI selection must override environment")
    
    def test_placeholder_rejection():
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        import os
        
        # Temporarily set placeholder value to test rejection
        original_value = os.environ.get('LOCAL_LLM')
        os.environ['LOCAL_LLM'] = 'your_model_name'
        
        try:
            config = Configuration.from_runnable_config(RunnableConfig(configurable={}))
            raise AssertionError("Should have failed with placeholder error")
        except ValueError as e:
            runner.assert_in('placeholder', str(e), "Error should mention placeholder")
        finally:
            # Restore original value
            if original_value is not None:
                os.environ['LOCAL_LLM'] = original_value
            else:
                os.environ.pop('LOCAL_LLM', None)
    
    def test_valid_model_selection():
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        runner.assert_equal(config.local_llm, 'gpt-oss:20b')
        runner.assert_equal(config.llm_provider, 'ollama')
    
    runner.run_test("UI Model Selection Override", test_ui_model_selection_override)
    runner.run_test("Placeholder Rejection", test_placeholder_rejection)
    runner.run_test("Valid Model Selection", test_valid_model_selection)
    
    return runner

def test_tavily_api():
    """Test Tavily API integration."""
    runner = TestRunner()
    
    def test_api_key_loading():
        api_key = os.getenv('TAVILY_API_KEY')
        runner.assert_true(api_key is not None, "TAVILY_API_KEY must be set")
        runner.assert_true(api_key.startswith('tvly-'), f"Invalid API key format: {api_key[:10]}...")
        runner.assert_greater(len(api_key), 20, "API key too short")
    
    def test_tavily_client_creation():
        from tavily import TavilyClient
        api_key = os.getenv('TAVILY_API_KEY')
        client = TavilyClient(api_key=api_key)
        runner.assert_true(client is not None, "TavilyClient creation failed")
    
    def test_tavily_search_function():
        from ollama_deep_researcher.utils import tavily_search
        
        result = tavily_search('artificial intelligence 2025', max_results=2)
        
        runner.assert_true(isinstance(result, dict), f"Expected dict, got {type(result)}")
        runner.assert_in('results', result, f"No 'results' key in response")
        runner.assert_greater(len(result['results']), 0, "No search results returned")
        
        first_result = result['results'][0]
        for field in ['title', 'url', 'content']:
            runner.assert_in(field, first_result, f"Missing field '{field}'")
    
    runner.run_test("API Key Loading", test_api_key_loading)
    runner.run_test("TavilyClient Creation", test_tavily_client_creation)
    runner.run_test("Tavily Search Function", test_tavily_search_function)
    
    return runner

def test_ollama_integration():
    """Test Ollama integration."""
    runner = TestRunner()
    
    def test_ollama_connection():
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(model='gpt-oss:20b', base_url='http://localhost:11434')
        result = llm.invoke('Hello')
        
        runner.assert_true(hasattr(result, 'content'), "No content attribute")
        runner.assert_greater(len(result.content), 0, "Empty response from Ollama")
    
    def test_get_llm_function():
        from ollama_deep_researcher.graph import get_llm
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        llm = get_llm(config)
        runner.assert_equal(llm.model, 'gpt-oss:20b', f"Wrong model: {llm.model}")
        
        result = llm.invoke('Hi')
        runner.assert_greater(len(result.content), 0, "Empty response from get_llm")
    
    def test_summarization_llm_no_json():
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        from langchain_ollama import ChatOllama
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        llm = ChatOllama(
            base_url=config.ollama_base_url,
            model=config.local_llm,
            temperature=0,
        )
        
        # Should NOT have format=json
        format_attr = getattr(llm, 'format', None)
        runner.assert_true(format_attr != 'json', f"Summarization LLM should not use JSON mode, got: {format_attr}")
        
        # Test natural text response
        result = llm.invoke('Summarize: AI is advancing rapidly.')
        
        # Should be natural text, not JSON
        import json
        try:
            json.loads(result.content)
            raise AssertionError("Summarization response should not be valid JSON")
        except (json.JSONDecodeError, ValueError):
            pass  # Expected
    
    runner.run_test("Ollama Connection", test_ollama_connection)
    runner.run_test("get_llm Function", test_get_llm_function)
    runner.run_test("Summarization LLM No JSON", test_summarization_llm_no_json)
    
    return runner

if __name__ == "__main__":
    print("🔬 UNIT TESTS - NO FALLBACKS, NO WORKAROUNDS")
    print("=" * 60)
    
    all_passed = True
    
    # Run all test suites
    config_runner = test_configuration()
    tavily_runner = test_tavily_api()
    ollama_runner = test_ollama_integration()
    
    # Combine results
    total_passed = config_runner.passed + tavily_runner.passed + ollama_runner.passed
    total_failed = config_runner.failed + tavily_runner.failed + ollama_runner.failed
    total_tests = total_passed + total_failed
    
    all_failures = config_runner.failures + tavily_runner.failures + ollama_runner.failures
    
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS: {total_passed}/{total_tests} passed")
    
    if total_failed > 0:
        print(f"\nALL FAILURES:")
        for name, error in all_failures:
            print(f"  ❌ {name}: {error}")
        sys.exit(1)
    else:
        print("🎉 ALL UNIT TESTS PASSED!")
        sys.exit(0)