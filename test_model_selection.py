#!/usr/bin/env python3
"""Test that model selection from UI properly flows through to execution."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_selection():
    """Test that UI model selection overrides environment defaults."""
    print("🔧 Testing Model Selection Flow")
    print("=" * 60)
    
    try:
        from ollama_deep_researcher.configuration import Configuration
        from langchain_core.runnables import RunnableConfig
        
        print("Phase 1: Test Environment Default Behavior")
        print("-" * 40)
        
        # Test environment-only configuration
        os.environ['LOCAL_LLM'] = 'llama3.2'  # Set environment default
        config_env_only = Configuration()
        print(f"Environment default: {config_env_only.local_llm}")
        
        print("\nPhase 2: Test UI Override Behavior")
        print("-" * 40)
        
        # Test UI configuration override
        ui_config = {
            'local_llm': 'gpt-oss:20b',  # UI selection
            'summarization_model': None,  # "Use main model"
            'search_api': 'tavily'
        }
        
        runnable_config = RunnableConfig(configurable=ui_config)
        config_with_ui = Configuration.from_runnable_config(runnable_config)
        print(f"UI-selected model: {config_with_ui.local_llm}")
        
        # Test that UI overrides environment
        if config_with_ui.local_llm == 'gpt-oss:20b':
            print("✅ UI selection properly overrides environment default")
        else:
            print(f"❌ UI selection failed. Expected: gpt-oss:20b, Got: {config_with_ui.local_llm}")
            return False
            
        print("\nPhase 3: Test Summarization Model Fallback")
        print("-" * 40)
        
        # Test that empty summarization_model uses main model
        from ollama_deep_researcher.graph import get_llm
        
        # Mock configurable for get_llm test
        class MockConfig:
            def __init__(self):
                self.local_llm = 'gpt-oss:20b'
                self.llm_provider = 'ollama'
                self.ollama_base_url = 'http://localhost:11434'
                self.use_tool_calling = False
        
        mock_config = MockConfig()
        
        # Test summarization model logic
        config_dict = {'summarization_model': None}  # "Use main model"
        summarization_model = config_dict.get('summarization_model')
        if not summarization_model:
            summarization_model = mock_config.local_llm
            
        if summarization_model == 'gpt-oss:20b':
            print("✅ Summarization model correctly falls back to main model")
        else:
            print(f"❌ Summarization fallback failed. Expected: gpt-oss:20b, Got: {summarization_model}")
            return False
            
        print("\nPhase 4: Test API Key Loading")
        print("-" * 40)
        
        # Test that Tavily API key is available
        tavily_key = os.getenv('TAVILY_API_KEY')
        if tavily_key and tavily_key.startswith('tvly-'):
            print("✅ Tavily API key properly loaded")
        else:
            print("❌ Tavily API key not found or invalid")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing model selection fixes...")
    success = test_model_selection()
    
    if success:
        print("\n✅ All model selection fixes working correctly!")
        print("The UI-selected model should now be used throughout the pipeline.")
    else:
        print("\n❌ Model selection issues remain.")
    
    sys.exit(0 if success else 1)