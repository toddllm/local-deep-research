#!/usr/bin/env python3
"""Debug Ollama invoke vs stream specific issue."""

import os
import sys
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

def test_ollama_methods():
    """Test different Ollama invocation methods."""
    print("=== TESTING OLLAMA METHODS ===")
    
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Test basic invoke
        print("Testing ChatOllama.invoke()...")
        llm = ChatOllama(
            base_url="http://localhost:11434",
            model="gpt-oss:20b",
            temperature=0,
        )
        
        messages = [
            SystemMessage(content="You are a helpful assistant. Respond with just 'Hello' and nothing else."),
            HumanMessage(content="Say hello")
        ]
        
        try:
            result = llm.invoke(messages)
            print(f"✅ Basic invoke works: {result.content[:50]}...")
        except Exception as e:
            print(f"❌ Basic invoke failed: {e}")
        
        # Test JSON mode invoke
        print("\nTesting ChatOllama.invoke() with JSON format...")
        llm_json = ChatOllama(
            base_url="http://localhost:11434",
            model="gpt-oss:20b",
            temperature=0,
            format="json"
        )
        
        json_messages = [
            SystemMessage(content='You are a helpful assistant. Respond with JSON format only: {"message": "your response"}'),
            HumanMessage(content="Say hello in JSON format")
        ]
        
        try:
            result = llm_json.invoke(json_messages)
            print(f"✅ JSON invoke works: {result.content[:50]}...")
        except Exception as e:
            print(f"❌ JSON invoke failed: {e}")
        
        # Test stream method
        print("\nTesting ChatOllama.stream()...")
        try:
            stream = llm.stream(messages)
            content = ""
            for chunk in stream:
                if hasattr(chunk, 'content'):
                    content += chunk.content
            print(f"✅ Stream works: {content[:50]}...")
        except Exception as e:
            print(f"❌ Stream failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Import or setup failed: {e}")
        return False

def test_in_flask_thread():
    """Test Ollama in background thread like Flask."""
    print("\n=== TESTING IN BACKGROUND THREAD ===")
    
    results = []
    
    def run_ollama_test():
        try:
            # Load environment
            load_dotenv()
            
            # Set environment variables explicitly  
            os.environ['LOCAL_LLM'] = 'gpt-oss:20b'
            
            result = test_ollama_methods()
            results.append(('thread_test', result))
        except Exception as e:
            print(f"❌ Thread test failed: {e}")
            results.append(('thread_test', False))
    
    thread = threading.Thread(target=run_ollama_test)
    thread.start()
    thread.join()
    
    return results

def test_configuration_integration():
    """Test with actual Configuration class."""
    print("\n=== TESTING CONFIGURATION INTEGRATION ===")
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        from ollama_deep_researcher.graph import get_llm
        
        config = Configuration()
        config.local_llm = 'gpt-oss:20b'
        config.use_tool_calling = False  # Use JSON mode
        
        runnable_config = RunnableConfig(configurable=config.__dict__)
        configurable = Configuration.from_runnable_config(runnable_config)
        
        print(f"Configuration: {configurable.local_llm}, JSON mode: {not configurable.use_tool_calling}")
        
        # Test get_llm function directly
        llm = get_llm(configurable)
        print(f"LLM created: {type(llm).__name__} with model {configurable.local_llm}")
        
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content='Respond with JSON: {"test": "success"}'),
            HumanMessage(content="Test")
        ]
        
        print("Testing get_llm invoke...")
        result = llm.invoke(messages)
        print(f"✅ get_llm invoke works: {result.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 OLLAMA INVOKE DEBUGGING")
    print("=" * 50)
    
    # Test main thread
    main_result = test_ollama_methods()
    
    # Test background thread
    thread_results = test_in_flask_thread()
    
    # Test configuration integration
    config_result = test_configuration_integration()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Main thread: {'✅ PASSED' if main_result else '❌ FAILED'}")
    print(f"  Background thread: {'✅ PASSED' if thread_results and thread_results[0][1] else '❌ FAILED'}")
    print(f"  Configuration: {'✅ PASSED' if config_result else '❌ FAILED'}")