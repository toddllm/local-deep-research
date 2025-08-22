#!/usr/bin/env python3
"""Debug Flask-specific environment issues."""

import os
import sys
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def simulate_flask_research_task():
    """Simulate the exact Flask research task environment."""
    print("=== SIMULATING FLASK RESEARCH TASK ===")
    
    # Load environment (as Flask app does)
    load_dotenv()
    
    # Set environment variables (as our fixed Flask does)
    env_vars = {
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'LOCAL_LLM': os.getenv('LOCAL_LLM'),
        'SEARCH_API': os.getenv('SEARCH_API'),
    }
    
    for key, value in env_vars.items():
        if value:
            os.environ[key] = value
    
    print(f"Environment check:")
    print(f"  TAVILY_API_KEY: {bool(os.getenv('TAVILY_API_KEY'))}")
    print(f"  LOCAL_LLM: {os.getenv('LOCAL_LLM', 'NOT_SET')}")
    
    # Test Tavily search (as utils.py does)
    try:
        from ollama_deep_researcher.utils import tavily_search
        print(f"  Testing tavily_search...")
        result = tavily_search('test query', max_results=1)
        print(f"  ✅ tavily_search works: {len(result.get('results', []))} results")
        return True
    except Exception as e:
        print(f"  ❌ tavily_search failed: {e}")
        return False

def simulate_flask_graph_execution():
    """Simulate the exact graph execution environment."""
    print("\n=== SIMULATING GRAPH EXECUTION ===")
    
    # Load environment
    load_dotenv()
    
    try:
        from ollama_deep_researcher.graph import graph
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        # Create configuration as Flask does
        ui_config = {
            'local_llm': 'gpt-oss:20b',
            'search_api': 'tavily',
            'max_web_research_loops': 1
        }
        
        config = Configuration()
        for key, value in ui_config.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        runnable_config = RunnableConfig(configurable=config.__dict__)
        
        print(f"Configuration:")
        print(f"  local_llm: {config.local_llm}")
        print(f"  search_api: {config.search_api}")
        
        # Test just the first step - query generation
        print(f"  Testing query generation...")
        from ollama_deep_researcher.graph import generate_query
        from ollama_deep_researcher.state import SummaryState
        
        state = SummaryState(
            research_topic='test topic',
            research_loop_count=0,
            query_history=[],
            sources_gathered=[],
            web_research_results=[],
            running_summary='',
            seen_urls=set()
        )
        
        result = generate_query(state, runnable_config)
        print(f"  ✅ Query generation works: {result.get('search_query', 'NO_QUERY')}")
        
        # Test web research step
        print(f"  Testing web research...")
        from ollama_deep_researcher.graph import web_research
        
        # Update state with generated query
        state.search_query = result.get('search_query', 'test query')
        
        web_result = web_research(state, runnable_config)
        print(f"  ✅ Web research works: {len(web_result.get('web_research_results', []))} results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 FLASK ENVIRONMENT DEBUGGING")
    print("=" * 50)
    
    # Run in background thread to simulate Flask
    results = []
    
    def run_tavily_test():
        results.append(('tavily', simulate_flask_research_task()))
    
    def run_graph_test():
        results.append(('graph', simulate_flask_graph_execution()))
    
    # Test in background threads
    thread1 = threading.Thread(target=run_tavily_test)
    thread1.start()
    thread1.join()
    
    thread2 = threading.Thread(target=run_graph_test)
    thread2.start()
    thread2.join()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")