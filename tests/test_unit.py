#!/usr/bin/env python3
"""Unit tests for core functions - NO FALLBACKS, NO WORKAROUNDS."""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

class TestConfiguration:
    """Test configuration system with strict validation."""
    
    def test_ui_model_selection_override(self):
        """UI selection MUST override environment defaults."""
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        # Set environment default
        os.environ['LOCAL_LLM'] = 'llama3.2'
        
        # UI override
        ui_config = {'local_llm': 'gpt-oss:20b'}
        runnable_config = RunnableConfig(configurable=ui_config)
        config = Configuration.from_runnable_config(runnable_config)
        
        assert config.local_llm == 'gpt-oss:20b', f"Expected gpt-oss:20b, got {config.local_llm}"
    
    def test_placeholder_rejection(self):
        """MUST reject placeholder values with clear error."""
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        # Empty config with placeholder in .env
        with pytest.raises(ValueError) as exc_info:
            config = Configuration.from_runnable_config(RunnableConfig(configurable={}))
        
        assert 'placeholder' in str(exc_info.value), f"Error should mention placeholder: {exc_info.value}"
    
    def test_valid_model_selection(self):
        """Valid model selection MUST work without issues."""
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        assert config.local_llm == 'gpt-oss:20b'
        assert config.llm_provider == 'ollama'


class TestTavilyAPI:
    """Test Tavily API integration with strict validation."""
    
    def test_api_key_loading(self):
        """API key MUST be available."""
        api_key = os.getenv('TAVILY_API_KEY')
        assert api_key is not None, "TAVILY_API_KEY environment variable not set"
        assert api_key.startswith('tvly-'), f"Invalid API key format: {api_key[:10]}..."
        assert len(api_key) > 20, f"API key too short: {len(api_key)} chars"
    
    def test_tavily_client_creation(self):
        """TavilyClient MUST create successfully."""
        from tavily import TavilyClient
        
        api_key = os.getenv('TAVILY_API_KEY')
        client = TavilyClient(api_key=api_key)
        assert client is not None
    
    def test_tavily_search_function(self):
        """utils.tavily_search MUST work without errors."""
        from ollama_deep_researcher.utils import tavily_search
        
        result = tavily_search('artificial intelligence 2025', max_results=2)
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert 'results' in result, f"No 'results' key in response: {result.keys()}"
        assert len(result['results']) > 0, "No search results returned"
        
        # Verify result structure
        first_result = result['results'][0]
        required_fields = ['title', 'url', 'content']
        for field in required_fields:
            assert field in first_result, f"Missing required field '{field}' in result: {first_result.keys()}"


class TestOllamaIntegration:
    """Test Ollama integration with strict validation."""
    
    def test_ollama_connection(self):
        """Ollama connection MUST work."""
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(model='gpt-oss:20b', base_url='http://localhost:11434')
        result = llm.invoke('Hello')
        
        assert hasattr(result, 'content'), f"No content attribute: {dir(result)}"
        assert len(result.content) > 0, "Empty response from Ollama"
    
    def test_get_llm_function(self):
        """get_llm function MUST create working LLM."""
        from ollama_deep_researcher.graph import get_llm
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        llm = get_llm(config)
        assert llm.model == 'gpt-oss:20b', f"Wrong model: {llm.model}"
        
        # Test that it works
        result = llm.invoke('Hi')
        assert len(result.content) > 0, "Empty response from get_llm"
    
    def test_summarization_llm_no_json(self):
        """Summarization LLM MUST NOT use JSON mode."""
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        from langchain_ollama import ChatOllama
        
        ui_config = {'local_llm': 'gpt-oss:20b'}
        config = Configuration.from_runnable_config(RunnableConfig(configurable=ui_config))
        
        # Create LLM as summarization does
        llm = ChatOllama(
            base_url=config.ollama_base_url,
            model=config.local_llm,
            temperature=0,
        )
        
        # Should NOT have format=json
        assert not hasattr(llm, 'format') or llm.format != 'json', f"Summarization LLM should not use JSON mode"
        
        # Test natural text response
        result = llm.invoke('Summarize: AI is advancing rapidly.')
        
        # Should be natural text, not JSON
        import json
        try:
            json.loads(result.content)
            pytest.fail("Summarization response should not be valid JSON")
        except (json.JSONDecodeError, ValueError):
            pass  # Expected - should not be JSON


class TestQueryGeneration:
    """Test query generation with strict validation."""
    
    def test_query_generation_structure(self):
        """Query generation MUST return proper structure."""
        from ollama_deep_researcher.graph import generate_query
        from ollama_deep_researcher.state import SummaryState
        from langchain_core.runnables import RunnableConfig
        
        state = SummaryState(
            research_topic='artificial intelligence software development',
            research_loop_count=0,
            query_history=[],
            sources_gathered=[],
            web_research_results=[],
            running_summary='',
            seen_urls=set()
        )
        
        ui_config = {'local_llm': 'gpt-oss:20b', 'use_tool_calling': False}
        config = RunnableConfig(configurable=ui_config)
        
        result = generate_query(state, config)
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert 'search_query' in result, f"No search_query in result: {result.keys()}"
        assert isinstance(result['search_query'], str), f"search_query not string: {type(result['search_query'])}"
        assert len(result['search_query']) > 10, f"Query too short: '{result['search_query']}'"
        
        # MUST NOT be the fallback query
        assert not result['search_query'].startswith('Tell me more about'), f"Using fallback query: '{result['search_query']}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])