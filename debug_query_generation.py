#!/usr/bin/env python3
"""Debug the specific query generation function that's failing."""

import os
import sys
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

def test_query_generation_direct():
    """Test the exact query generation function that's failing."""
    print("=== TESTING QUERY GENERATION FUNCTION ===")
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from ollama_deep_researcher.graph import generate_search_query_with_structured_output, Query
        from ollama_deep_researcher.prompts import query_writer_instructions, json_mode_query_instructions
        from langchain_core.messages import SystemMessage, HumanMessage
        from langchain_core.runnables import RunnableConfig
        from pydantic import BaseModel, Field
        from langchain_core.tools import tool
        import json
        
        # Create test configuration
        config = Configuration()
        config.local_llm = 'gpt-oss:20b'
        config.use_tool_calling = False  # Use JSON mode like in graph
        
        # Test tool class - same as in generate_query
        @tool
        class Query(BaseModel):
            """This tool is used to generate a query for web search."""
            query: str = Field(description="The actual search query string")
            rationale: str = Field(description="Brief explanation of why this query is relevant")
        
        # Create test messages - same format as in generate_query
        current_date = "2025-01-22"
        research_topic = "test topic"
        
        formatted_prompt = query_writer_instructions.format(
            current_date=current_date, research_topic=research_topic
        )
        
        messages = [
            SystemMessage(content=formatted_prompt + json_mode_query_instructions),
            HumanMessage(content="Generate a query for web search:"),
        ]
        
        print(f"Configuration: model={config.local_llm}, tool_calling={config.use_tool_calling}")
        print(f"Messages created, testing function...")
        
        # Test the exact function that's failing
        result = generate_search_query_with_structured_output(
            configurable=config,
            messages=messages,
            tool_class=Query,
            fallback_query=f"Tell me more about {research_topic}",
            tool_query_field="query",
            json_query_field="query",
            query_model=None,
        )
        
        print(f"✅ Query generation works: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Query generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_in_flask_context():
    """Test in background thread with Flask-like environment."""
    print("\n=== TESTING IN FLASK-LIKE CONTEXT ===")
    
    results = []
    
    def run_flask_test():
        try:
            # Set environment like Flask does
            load_dotenv()
            env_vars = {
                'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
                'LOCAL_LLM': 'gpt-oss:20b',
                'SEARCH_API': 'tavily',
            }
            
            for key, value in env_vars.items():
                if value:
                    os.environ[key] = value
            
            result = test_query_generation_direct()
            results.append(('flask_context', result))
            
        except Exception as e:
            print(f"❌ Flask context test failed: {e}")
            results.append(('flask_context', False))
    
    thread = threading.Thread(target=run_flask_test)
    thread.start()
    thread.join()
    
    return results

def test_graph_state_integration():
    """Test with actual graph state like in Flask."""
    print("\n=== TESTING GRAPH STATE INTEGRATION ===")
    
    try:
        from ollama_deep_researcher.state import SummaryState
        from ollama_deep_researcher.graph import generate_query
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        # Create state like Flask does
        state = SummaryState(
            research_topic='test topic for debugging',
            research_loop_count=0,
            query_history=[],
            sources_gathered=[],
            web_research_results=[],
            running_summary='',
            seen_urls=set()
        )
        
        # Create config like Flask does
        config = Configuration()
        config.local_llm = 'gpt-oss:20b'
        config.search_api = 'tavily'
        config.max_web_research_loops = 1
        
        config_dict = {**config.__dict__, 'progress_callback': lambda x, y=None, z=None: print(f"Progress: {x}")}
        runnable_config = RunnableConfig(configurable=config_dict)
        
        print(f"State created: {state.research_topic}")
        print(f"Config: {config.local_llm}")
        
        # Test the actual generate_query function
        result = generate_query(state, runnable_config)
        print(f"✅ Graph state integration works: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Graph state integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 QUERY GENERATION DEBUGGING")
    print("=" * 50)
    
    # Test direct function
    direct_result = test_query_generation_direct()
    
    # Test in Flask context
    flask_results = test_in_flask_context()
    
    # Test graph integration
    graph_result = test_graph_state_integration()
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Direct function: {'✅ PASSED' if direct_result else '❌ FAILED'}")
    print(f"  Flask context: {'✅ PASSED' if flask_results and flask_results[0][1] else '❌ FAILED'}")
    print(f"  Graph integration: {'✅ PASSED' if graph_result else '❌ FAILED'}")