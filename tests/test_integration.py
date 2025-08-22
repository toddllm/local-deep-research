#!/usr/bin/env python3
"""Integration tests for Flask endpoints - NO FALLBACKS, NO WORKAROUNDS."""

import sys
import os
import time
import requests
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

class IntegrationTestRunner:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
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
    
    def assert_status_code(self, response, expected_code):
        if response.status_code != expected_code:
            raise AssertionError(f"Expected status {expected_code}, got {response.status_code}: {response.text}")
    
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
    
    def wait_for_research_completion(self, task_id, timeout=300):  # 5 minute timeout for LLMs
        """Wait for research to complete with extended timeout for LLMs."""
        start_time = time.time()
        last_status = "unknown"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/api/research/{task_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    if status != last_status:
                        print(f"    Status: {status}")
                        last_status = status
                    
                    if status == 'completed':
                        return data
                    elif status == 'failed':
                        error = data.get('error', 'Unknown error')
                        raise AssertionError(f"Research failed: {error}")
                    
                time.sleep(2)  # Check every 2 seconds
            except requests.exceptions.RequestException as e:
                print(f"    Warning: Request failed: {e}")
                time.sleep(5)
        
        raise AssertionError(f"Research timed out after {timeout} seconds")

def test_flask_endpoints():
    """Test Flask API endpoints."""
    runner = IntegrationTestRunner()
    
    def test_health_endpoint():
        response = requests.get(f"{runner.base_url}/health", timeout=10)
        runner.assert_status_code(response, 200)
        
        data = response.json()
        runner.assert_equal(data['status'], 'healthy')
        runner.assert_in('timestamp', data)
    
    def test_config_endpoint():
        response = requests.get(f"{runner.base_url}/api/config", timeout=10)
        runner.assert_status_code(response, 200)
        
        data = response.json()
        required_fields = ['llm_provider', 'local_llm', 'search_api', 'max_loops']
        for field in required_fields:
            runner.assert_in(field, data, f"Missing config field: {field}")
    
    def test_models_endpoint():
        response = requests.get(f"{runner.base_url}/api/models", timeout=10)
        runner.assert_status_code(response, 200)
        
        data = response.json()
        runner.assert_in('models', data)
        runner.assert_true(isinstance(data['models'], list))
        runner.assert_true(len(data['models']) > 0, "No models available")
        
        # Check that our test model is available
        runner.assert_in('gpt-oss:20b', data['models'], "Test model gpt-oss:20b not available")
    
    def test_search_providers_endpoint():
        response = requests.get(f"{runner.base_url}/api/search-providers", timeout=10)
        runner.assert_status_code(response, 200)
        
        data = response.json()
        runner.assert_in('providers', data)
        runner.assert_in('current', data)
        
        # Tavily should be available with API key
        runner.assert_in('tavily', data['providers'], "Tavily provider not available")
    
    runner.run_test("Health Endpoint", test_health_endpoint)
    runner.run_test("Config Endpoint", test_config_endpoint)
    runner.run_test("Models Endpoint", test_models_endpoint)
    runner.run_test("Search Providers Endpoint", test_search_providers_endpoint)
    
    return runner

def test_research_api():
    """Test research API with real requests."""
    runner = IntegrationTestRunner()
    
    def test_research_start():
        research_data = {
            'topic': 'artificial intelligence testing',
            'config': {
                'local_llm': 'gpt-oss:20b',
                'search_api': 'tavily',
                'max_web_research_loops': 1
            }
        }
        
        response = requests.post(
            f"{runner.base_url}/api/research",
            json=research_data,
            timeout=10
        )
        
        runner.assert_status_code(response, 200)
        data = response.json()
        runner.assert_in('task_id', data)
        
        return data['task_id']
    
    def test_research_status():
        # Start a research task
        task_id = test_research_start()
        
        # Check status immediately
        response = requests.get(f"{runner.base_url}/api/research/{task_id}", timeout=10)
        runner.assert_status_code(response, 200)
        
        data = response.json()
        runner.assert_in('status', data)
        runner.assert_in('topic', data)
        runner.assert_in('id', data)
        
        # Status should be pending or running
        status = data['status']
        runner.assert_true(status in ['pending', 'running'], f"Unexpected initial status: {status}")
    
    def test_research_completion_with_tavily():
        """Test complete research pipeline with Tavily API - MUST WORK."""
        research_data = {
            'topic': 'machine learning software testing',
            'config': {
                'local_llm': 'gpt-oss:20b',
                'search_api': 'tavily',  # MUST use Tavily
                'max_web_research_loops': 1
            }
        }
        
        print(f"    Starting research with Tavily API...")
        response = requests.post(
            f"{runner.base_url}/api/research",
            json=research_data,
            timeout=10
        )
        
        runner.assert_status_code(response, 200)
        data = response.json()
        task_id = data['task_id']
        
        print(f"    Task ID: {task_id}")
        print(f"    Waiting for completion (5 min timeout for LLM processing)...")
        
        # Wait for completion with extended timeout
        final_data = runner.wait_for_research_completion(task_id, timeout=300)
        
        # Verify results
        runner.assert_equal(final_data['status'], 'completed')
        runner.assert_in('result', final_data)
        
        result = final_data['result']
        runner.assert_true(len(result) > 100, f"Result too short: {len(result)} chars")
        
        # Check activity log for Tavily success
        if 'activity_log' in final_data:
            tavily_errors = []
            tavily_success = []
            
            for entry in final_data['activity_log']:
                message = entry.get('message', '')
                if 'tavily' in message.lower():
                    if 'error' in message.lower() or 'unauthorized' in message.lower():
                        tavily_errors.append(message)
                    elif 'found' in message.lower() or 'successful' in message.lower():
                        tavily_success.append(message)
            
            if tavily_errors:
                raise AssertionError(f"Tavily API errors found: {tavily_errors}")
            
            runner.assert_true(len(tavily_success) > 0, f"No successful Tavily searches found in logs")
            print(f"    ✅ Tavily API working: {len(tavily_success)} successful searches")
        
        # Verify model selection
        model_logs = [e for e in final_data.get('activity_log', []) 
                     if 'invoking' in e.get('message', '').lower()]
        
        for log in model_logs:
            message = log.get('message', '')
            if 'gpt-oss:20b' not in message:
                raise AssertionError(f"Wrong model used: {message}")
        
        print(f"    ✅ Model selection working: gpt-oss:20b used")
        print(f"    ✅ Research completed: {len(result)} char result")
    
    def test_invalid_request():
        # Test with missing topic
        response = requests.post(
            f"{runner.base_url}/api/research",
            json={'config': {'local_llm': 'gpt-oss:20b'}},
            timeout=10
        )
        
        runner.assert_status_code(response, 400)
    
    def test_nonexistent_task():
        response = requests.get(f"{runner.base_url}/api/research/nonexistent-id", timeout=10)
        runner.assert_status_code(response, 404)
    
    runner.run_test("Research Start", test_research_start)
    runner.run_test("Research Status", test_research_status) 
    runner.run_test("Research Completion with Tavily", test_research_completion_with_tavily)
    runner.run_test("Invalid Request", test_invalid_request)
    runner.run_test("Nonexistent Task", test_nonexistent_task)
    
    return runner

def test_model_configuration():
    """Test model configuration through API."""
    runner = IntegrationTestRunner()
    
    def test_model_selection_persistence():
        """Test that model selection persists through research."""
        research_data = {
            'topic': 'quick test',
            'config': {
                'local_llm': 'gpt-oss:20b',  # Specific model selection
                'search_api': 'duckduckgo',  # Use DuckDuckGo to avoid API issues
                'max_web_research_loops': 1
            }
        }
        
        response = requests.post(
            f"{runner.base_url}/api/research",
            json=research_data,
            timeout=10
        )
        
        runner.assert_status_code(response, 200)
        task_id = response.json()['task_id']
        
        # Wait for completion
        final_data = runner.wait_for_research_completion(task_id, timeout=180)
        
        # Check that correct model was used
        if 'activity_log' in final_data:
            model_mentions = []
            for entry in final_data['activity_log']:
                message = entry.get('message', '')
                if 'invoking' in message.lower() and 'gpt-oss:20b' in message:
                    model_mentions.append(message)
            
            runner.assert_true(len(model_mentions) > 0, 
                             "Selected model gpt-oss:20b not found in activity logs")
            print(f"    ✅ Model selection persisted: {len(model_mentions)} uses")
    
    runner.run_test("Model Selection Persistence", test_model_selection_persistence)
    
    return runner

if __name__ == "__main__":
    print("🔬 INTEGRATION TESTS - NO FALLBACKS, NO WORKAROUNDS")
    print("=" * 60)
    
    try:
        # Test Flask app availability
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code != 200:
            print("❌ Flask app not available on localhost:5001")
            print("Please start the app with: python app.py")
            sys.exit(1)
        print("✅ Flask app is running")
    except requests.exceptions.RequestException:
        print("❌ Flask app not available on localhost:5001")
        print("Please start the app with: python app.py")
        sys.exit(1)
    
    all_passed = True
    
    # Run all test suites
    endpoint_runner = test_flask_endpoints()
    research_runner = test_research_api()
    config_runner = test_model_configuration()
    
    # Combine results
    total_passed = endpoint_runner.passed + research_runner.passed + config_runner.passed
    total_failed = endpoint_runner.failed + research_runner.failed + config_runner.failed
    total_tests = total_passed + total_failed
    
    all_failures = endpoint_runner.failures + research_runner.failures + config_runner.failures
    
    print(f"\n{'='*60}")
    print(f"INTEGRATION RESULTS: {total_passed}/{total_tests} passed")
    
    if total_failed > 0:
        print(f"\nALL FAILURES:")
        for name, error in all_failures:
            print(f"  ❌ {name}: {error}")
        sys.exit(1)
    else:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        sys.exit(0)