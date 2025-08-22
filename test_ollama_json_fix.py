#!/usr/bin/env python3
"""Test Ollama JSON format issue and potential fixes."""

import requests
import json

def test_ollama_without_json_format():
    """Test without JSON format parameter."""
    print("=== TESTING WITHOUT JSON FORMAT ===")
    
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "system",
                "content": "You MUST respond with valid JSON format. Format your response as a JSON object with these exact keys:\n- \"query\": The actual search query string\n- \"rationale\": Brief explanation of why this query is relevant\n\nDo not include any text before or after the JSON object."
            },
            {
                "role": "user", 
                "content": "Generate a search query for: test topic for debugging"
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            message_content = data.get('message', {}).get('content', '')
            print(f"✅ Non-JSON format works: {message_content[:200]}...")
            
            # Try to parse JSON
            try:
                parsed = json.loads(message_content)
                query = parsed.get('query', '')
                print(f"✅ JSON parsing works: query='{query}'")
                return True, message_content
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Raw content: {message_content}")
                return False, message_content
        else:
            print(f"❌ API call failed: {response.status_code} - {response.text}")
            return False, ""
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False, ""

def test_ollama_with_json_format():
    """Test with JSON format parameter."""
    print("\n=== TESTING WITH JSON FORMAT ===")
    
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "system",
                "content": "Format your response as a JSON object with these exact keys:\n- \"query\": The actual search query string\n- \"rationale\": Brief explanation of why this query is relevant"
            },
            {
                "role": "user", 
                "content": "Generate a search query for: test topic for debugging"
            }
        ],
        "format": "json",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            message_content = data.get('message', {}).get('content', '')
            print(f"Raw response: {data}")
            print(f"Message content: '{message_content}'")
            
            if message_content:
                try:
                    parsed = json.loads(message_content)
                    query = parsed.get('query', '')
                    print(f"✅ JSON format works: query='{query}'")
                    return True, message_content
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    return False, message_content
            else:
                print(f"❌ Empty content with JSON format")
                return False, ""
        else:
            print(f"❌ API call failed: {response.status_code} - {response.text}")
            return False, ""
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False, ""

if __name__ == "__main__":
    print("🔬 OLLAMA JSON FORMAT DEBUGGING")
    print("=" * 50)
    
    no_json_result, no_json_content = test_ollama_without_json_format()
    json_result, json_content = test_ollama_with_json_format()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Without JSON format: {'✅ PASSED' if no_json_result else '❌ FAILED'}")
    print(f"  With JSON format: {'✅ PASSED' if json_result else '❌ FAILED'}")
    
    if not json_result and no_json_result:
        print(f"\n💡 SOLUTION: Use prompt-based JSON instead of format parameter")
        print(f"Working content: {no_json_content[:200]}...")