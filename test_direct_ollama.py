#!/usr/bin/env python3
"""Test direct Ollama API to bypass LangChain streaming issues."""

import requests
import json

def test_direct_ollama_api():
    """Test using Ollama API directly."""
    print("=== TESTING DIRECT OLLAMA API ===")
    
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
            print(f"✅ Direct API works: {message_content[:100]}...")
            
            # Try to parse JSON
            try:
                parsed = json.loads(message_content)
                query = parsed.get('query', '')
                print(f"✅ JSON parsing works: query='{query}'")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Raw content: {message_content}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        return False

def test_direct_ollama_streaming():
    """Test direct streaming API."""
    print("\n=== TESTING DIRECT OLLAMA STREAMING ===")
    
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "system",
                "content": "Respond with just: Hello from streaming"
            },
            {
                "role": "user", 
                "content": "Say hello"
            }
        ],
        "stream": True
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        
        if response.status_code == 200:
            content = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get('message', {}).get('content', '')
                        content += delta
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Direct streaming works: {content[:100]}...")
            return True
        else:
            print(f"❌ Streaming API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Direct streaming test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔬 DIRECT OLLAMA API TESTING")
    print("=" * 50)
    
    non_stream_result = test_direct_ollama_api()
    stream_result = test_direct_ollama_streaming()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Non-streaming: {'✅ PASSED' if non_stream_result else '❌ FAILED'}")
    print(f"  Streaming: {'✅ PASSED' if stream_result else '❌ FAILED'}")