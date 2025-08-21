#!/usr/bin/env python3
"""Flask web application for Local Deep Researcher."""

import sys
import os
import json
import threading
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import research components
from ollama_deep_researcher.graph import graph
from ollama_deep_researcher.configuration import Configuration
from langchain_core.runnables import RunnableConfig

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Store research tasks (in production, use Redis or database)
research_tasks = {}

def run_research_task(task_id, topic, custom_config=None):
    """Run research in background thread."""
    try:
        # Update status
        research_tasks[task_id]['status'] = 'running'
        research_tasks[task_id]['started_at'] = datetime.now().isoformat()
        research_tasks[task_id]['activity_log'] = []
        
        def log_activity(message, detail=None):
            """Log activity with timestamp"""
            entry = {
                'time': datetime.now().isoformat(),
                'message': message
            }
            if detail:
                entry['detail'] = detail
            research_tasks[task_id]['activity_log'].append(entry)
            research_tasks[task_id]['progress'] = message
        
        # Create configuration - use custom config if provided
        config = Configuration()
        
        # Apply custom configuration if provided
        search_apis = None
        summarization_model = None
        query_model = None
        if custom_config:
            if 'local_llm' in custom_config:
                config.local_llm = custom_config['local_llm']
            if 'summarization_model' in custom_config:
                summarization_model = custom_config['summarization_model']
            if 'query_model' in custom_config:
                query_model = custom_config['query_model']
            if 'search_apis' in custom_config and custom_config['search_apis']:
                # Multi-source mode
                search_apis = custom_config['search_apis']
                log_activity(f'🌐 Advanced Mode: Multi-source search', f'APIs: {", ".join(search_apis)}')
            elif 'search_api' in custom_config:
                config.search_api = custom_config['search_api']
            if 'max_web_research_loops' in custom_config:
                config.max_web_research_loops = custom_config['max_web_research_loops']
        
        if search_apis:
            log_activity(f'🔧 Initializing with {config.local_llm} model', f'Multi-source search: {", ".join(search_apis)}')
        else:
            log_activity(f'🔧 Initializing with {config.local_llm} model', f'Search API: {config.search_api}')
        
        runnable_config = RunnableConfig(configurable=config.__dict__)
        
        # Prepare input
        input_data = {"research_topic": topic}
        
        # Add progress updates
        log_activity('🤔 Generating optimized search query...', f'Topic: {topic}')
        
        # Inject progress callback into config
        def progress_callback(step, detail=None, verbose_data=None):
            """Callback for graph progress updates"""
            # Store verbose data separately for expandable view
            entry = {
                'time': datetime.now().isoformat(),
                'message': step
            }
            if detail:
                entry['detail'] = detail
            if verbose_data:
                entry['verbose'] = verbose_data
            research_tasks[task_id]['activity_log'].append(entry)
            research_tasks[task_id]['progress'] = step
        
        # Store callback and search_apis in configurable for graph nodes to use
        config_dict = {**config.__dict__, 'progress_callback': progress_callback}
        if search_apis:
            config_dict['search_apis'] = search_apis
        if summarization_model:
            config_dict['summarization_model'] = summarization_model
        if query_model:
            config_dict['query_model'] = query_model
        runnable_config = RunnableConfig(configurable=config_dict)
        
        # Run the graph with streaming updates
        log_activity('🚀 Starting research pipeline...', 'Initializing LangGraph workflow')
        log_activity('📊 Configuration details', f'Model: {config.local_llm}, API: {config.search_api}, Loops: {config.max_web_research_loops}')
        
        try:
            # More verbose logging
            log_activity('📝 Analyzing research topic...', f'Full topic: {topic}')
            log_activity('🧠 Preparing LLM context', f'Loading model {config.local_llm} with JSON output mode')
            
            result = graph.invoke(input_data, runnable_config)
            
            log_activity('✅ Research pipeline complete', 'Processing and formatting final results...')
        except Exception as e:
            log_activity('❌ Error in research pipeline', str(e))
            raise
        
        # Store results
        if result and "running_summary" in result:
            log_activity('💾 Saving research results...', 'Formatting and storing output')
            
            research_tasks[task_id]['status'] = 'completed'
            research_tasks[task_id]['result'] = result["running_summary"]
            research_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"research_output_{timestamp}.md"
            with open(output_file, "w") as f:
                f.write(f"# Research Report: {topic}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(result["running_summary"])
            research_tasks[task_id]['output_file'] = output_file
            
            log_activity('🎉 Research complete!', f'Results saved to {output_file}')
        else:
            research_tasks[task_id]['status'] = 'failed'
            research_tasks[task_id]['error'] = 'No summary generated'
            
    except Exception as e:
        research_tasks[task_id]['status'] = 'failed'
        research_tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    config = Configuration()
    return jsonify({
        'llm_provider': config.llm_provider,
        'local_llm': config.local_llm,
        'search_api': config.search_api,
        'max_loops': config.max_web_research_loops,
        'validate_sources': True  # Our new feature!
    })

@app.route('/api/research', methods=['POST'])
def start_research():
    """Start a new research task."""
    data = request.json
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # Get configuration from request or environment
    custom_config = {}
    if 'config' in data:
        custom_config = data['config']
        # Handle advanced mode with multiple search APIs
        if 'search_apis' in custom_config and custom_config['search_apis']:
            # Pass through for multi-source aggregation
            pass
        elif 'search_api' in custom_config:
            # Single API mode
            pass
    else:
        # Check environment for current settings
        if os.getenv('LOCAL_LLM'):
            custom_config['local_llm'] = os.getenv('LOCAL_LLM')
        if os.getenv('SEARCH_API'):
            custom_config['search_api'] = os.getenv('SEARCH_API')
        if os.getenv('MAX_WEB_RESEARCH_LOOPS'):
            custom_config['max_web_research_loops'] = int(os.getenv('MAX_WEB_RESEARCH_LOOPS'))
    
    # Create task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task
    research_tasks[task_id] = {
        'id': task_id,
        'topic': topic,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'progress': 'Initializing...'
    }
    
    # Start research in background thread with custom config
    thread = threading.Thread(target=run_research_task, args=(task_id, topic, custom_config))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/api/research/<task_id>', methods=['GET'])
def get_research_status(task_id):
    """Get status of a research task."""
    if task_id not in research_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = research_tasks[task_id]
    response = {
        'id': task['id'],
        'topic': task['topic'],
        'status': task['status'],
        'created_at': task['created_at']
    }
    
    if 'progress' in task:
        response['progress'] = task['progress']
    
    if 'activity_log' in task:
        response['activity_log'] = task['activity_log']
    
    if task['status'] == 'completed':
        response['result'] = task['result']
        if 'output_file' in task:
            response['output_file'] = task['output_file']
    elif task['status'] == 'failed':
        response['error'] = task.get('error', 'Unknown error')
    
    return jsonify(response)

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available Ollama models."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({'models': [m['name'] for m in models]})
    except:
        # Return default models if Ollama is not running
        return jsonify({'models': ['llama3.2', 'llama3.1:8b', 'mistral', 'phi']})
    return jsonify({'models': []})

@app.route('/api/search-providers', methods=['GET'])
def get_search_providers():
    """Get available search providers based on API keys."""
    providers = ['duckduckgo', 'arxiv']  # Always available (no API key needed)
    
    # Check for API keys in environment
    if os.getenv('TAVILY_API_KEY'):
        providers.insert(0, 'tavily')  # Put Tavily first if available
    if os.getenv('PERPLEXITY_API_KEY'):
        providers.append('perplexity')
    if os.getenv('SEARXNG_URL'):
        providers.append('searxng')
    
    # Get current default from config
    config = Configuration()
    current = config.search_api
    
    return jsonify({
        'providers': providers,
        'current': current
    })

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Update configuration settings."""
    data = request.json
    
    # Update environment variables for the current session
    if 'local_llm' in data:
        os.environ['LOCAL_LLM'] = data['local_llm']
    if 'search_api' in data:
        os.environ['SEARCH_API'] = data['search_api']
    if 'max_web_research_loops' in data:
        os.environ['MAX_WEB_RESEARCH_LOOPS'] = str(data['max_web_research_loops'])
    
    return jsonify({'status': 'success'})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Local Deep Researcher Web Interface")
    print("📍 Visit http://localhost:5001 to access the application")
    app.run(debug=True, host='0.0.0.0', port=5001)