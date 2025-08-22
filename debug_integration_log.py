#!/usr/bin/env python3
"""Debug integration test log checking."""

import requests
import json
import time

def test_and_examine_log():
    """Start a research task and examine the activity log."""
    print("=== STARTING RESEARCH AND EXAMINING LOG ===")
    
    base_url = "http://localhost:5001"
    
    # Start research
    research_data = {
        'topic': 'machine learning software testing',
        'config': {
            'local_llm': 'gpt-oss:20b',
            'search_api': 'tavily',
            'max_web_research_loops': 1
        }
    }
    
    print("Starting research...")
    response = requests.post(f"{base_url}/api/research", json=research_data, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to start research: {response.status_code}")
        return False
    
    data = response.json()
    task_id = data['task_id']
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    print("Waiting for completion...")
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{base_url}/api/research/{task_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            
            if status == 'completed':
                print(f"✅ Research completed!")
                
                # Examine activity log
                activity_log = data.get('activity_log', [])
                print(f"\nActivity log has {len(activity_log)} entries:")
                
                tavily_entries = []
                for i, entry in enumerate(activity_log):
                    message = entry.get('message', '')
                    detail = entry.get('detail', '')
                    
                    print(f"  {i+1}. {message}")
                    if detail:
                        print(f"     Detail: {detail}")
                    
                    # Check for Tavily mentions
                    if 'tavily' in message.lower() or 'tavily' in detail.lower():
                        tavily_entries.append(entry)
                        print(f"     ^^ TAVILY MENTION")
                
                print(f"\nTavily-related entries: {len(tavily_entries)}")
                for entry in tavily_entries:
                    print(f"  - {entry.get('message', '')}: {entry.get('detail', '')}")
                
                # Check for success/found patterns
                success_patterns = ['found', 'successful', 'complete', 'results']
                error_patterns = ['error', 'unauthorized', 'failed']
                
                tavily_successes = []
                tavily_errors = []
                
                for entry in activity_log:
                    message = entry.get('message', '').lower()
                    detail = entry.get('detail', '').lower()
                    full_text = f"{message} {detail}"
                    
                    if 'tavily' in full_text:
                        has_success = any(pattern in full_text for pattern in success_patterns)
                        has_error = any(pattern in full_text for pattern in error_patterns)
                        
                        if has_success:
                            tavily_successes.append(entry)
                        elif has_error:
                            tavily_errors.append(entry)
                
                print(f"\nTavily successes: {len(tavily_successes)}")
                for entry in tavily_successes:
                    print(f"  ✅ {entry.get('message', '')}: {entry.get('detail', '')}")
                
                print(f"\nTavily errors: {len(tavily_errors)}")
                for entry in tavily_errors:
                    print(f"  ❌ {entry.get('message', '')}: {entry.get('detail', '')}")
                
                return len(tavily_successes) > 0
                
            elif status == 'failed':
                error = data.get('error', 'Unknown error')
                print(f"❌ Research failed: {error}")
                return False
        
        time.sleep(2)
    
    print(f"❌ Timed out after {timeout} seconds")
    return False

if __name__ == "__main__":
    print("🔬 INTEGRATION LOG DEBUGGING")
    print("=" * 50)
    
    success = test_and_examine_log()
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}")