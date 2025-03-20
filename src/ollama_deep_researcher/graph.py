import json

from typing_extensions import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph

from ollama_deep_researcher.configuration import Configuration, SearchAPI
from ollama_deep_researcher.utils import deduplicate_and_format_sources, tavily_search, format_sources, perplexity_search, duckduckgo_search, searxng_search, strip_thinking_tokens, get_config_value
from ollama_deep_researcher.state import SummaryState, SummaryStateInput, SummaryStateOutput
from ollama_deep_researcher.prompts import query_writer_instructions, summarizer_instructions, reflection_instructions, get_current_date
from ollama_deep_researcher.lmstudio import ChatLMStudio

# Nodes
def generate_query(state: SummaryState, config: RunnableConfig):
    """ Generate a query for web search """

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=state.research_topic
    )

    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    
    # Choose the appropriate LLM based on the provider
    if configurable.llm_provider == "lmstudio":
        llm_json_mode = ChatLMStudio(
            base_url=configurable.lmstudio_base_url, 
            model=configurable.local_llm, 
            temperature=0, 
            format="json"
        )
    else: # Default to Ollama
        llm_json_mode = ChatOllama(
            base_url=configurable.ollama_base_url, 
            model=configurable.local_llm, 
            temperature=0, 
            format="json"
        )
    
    result = llm_json_mode.invoke(
        [SystemMessage(content=formatted_prompt),
        HumanMessage(content=f"Generate a query for web search:")]
    )
    
    # Strip thinking tokens if configured
    content = result.content
    if configurable.strip_thinking_tokens:
        content = strip_thinking_tokens(content)
    
    # Parse the JSON response
    try:
        query = json.loads(content)
        search_query = query['query']
    except (json.JSONDecodeError, KeyError):
        # Fallback for models that don't follow the structured output format
        search_query = content
    return {"search_query": search_query}

def web_research(state: SummaryState, config: RunnableConfig):
    """ Gather information from the web """

    # Configure
    configurable = Configuration.from_runnable_config(config)

    # Get the search API
    search_api = get_config_value(configurable.search_api)

    # Search the web
    if search_api == "tavily":
        search_results = tavily_search(state.search_query, include_raw_content=True, max_results=1)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=True)
    elif search_api == "perplexity":
        search_results = perplexity_search(state.search_query, state.research_loop_count)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=False)
    elif search_api == "duckduckgo":
        search_results = duckduckgo_search(state.search_query, max_results=3, fetch_full_page=configurable.fetch_full_page)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=True)
    elif search_api == "searxng":
        search_results = searxng_search(state.search_query, max_results=3, fetch_full_page=configurable.fetch_full_page)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=False)
    else:
        raise ValueError(f"Unsupported search API: {configurable.search_api}")

    return {"sources_gathered": [format_sources(search_results)], "research_loop_count": state.research_loop_count + 1, "web_research_results": [search_str]}

def summarize_sources(state: SummaryState, config: RunnableConfig):
    """ Summarize the gathered sources """

    # Existing summary
    existing_summary = state.running_summary

    # Most recent web research
    most_recent_web_research = state.web_research_results[-1]

    # Build the human message
    if existing_summary:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )

    # Run the LLM
    configurable = Configuration.from_runnable_config(config)
    
    # Choose the appropriate LLM based on the provider
    if configurable.llm_provider == "lmstudio":
        llm = ChatLMStudio(
            base_url=configurable.lmstudio_base_url, 
            model=configurable.local_llm, 
            temperature=0
        )
    else:  # Default to Ollama
        llm = ChatOllama(
            base_url=configurable.ollama_base_url, 
            model=configurable.local_llm, 
            temperature=0
        )
    
    result = llm.invoke(
        [SystemMessage(content=summarizer_instructions),
        HumanMessage(content=human_message_content)]
    )

    # Strip thinking tokens if configured
    running_summary = result.content
    if configurable.strip_thinking_tokens:
        running_summary = strip_thinking_tokens(running_summary)

    return {"running_summary": running_summary}

def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """ Reflect on the summary and generate a follow-up query """

    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    
    # Choose the appropriate LLM based on the provider
    if configurable.llm_provider == "lmstudio":
        llm_json_mode = ChatLMStudio(
            base_url=configurable.lmstudio_base_url, 
            model=configurable.local_llm, 
            temperature=0, 
            format="json"
        )
    else:  # Default to Ollama
        llm_json_mode = ChatOllama(
            base_url=configurable.ollama_base_url, 
            model=configurable.local_llm, 
            temperature=0, 
            format="json"
        )
    
    result = llm_json_mode.invoke(
        [SystemMessage(content=reflection_instructions.format(research_topic=state.research_topic)),
        HumanMessage(content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}")]
    )
    
    # Strip thinking tokens if configured
    reflection_content = result.content
    if configurable.strip_thinking_tokens:
        reflection_content = strip_thinking_tokens(reflection_content)
    
    try:
        query = reflection_content.get('follow_up_query')
        
        # JSON mode can fail in some cases
        if not query:
            # Fallback to a placeholder query
            return {"search_query": f"Tell me more about {state.research_topic}"}
        
        return {"search_query": query}
    
    except (json.JSONDecodeError, KeyError):
        # Fallback for models that don't follow the structured output format or malformed JSON
        return {"search_query": f"Tell me more about {state.research_topic}"}

def finalize_summary(state: SummaryState):
    """ Finalize the summary """

    # Deduplicate sources before joining
    seen_sources = set()
    unique_sources = []
    
    for source in state.sources_gathered:
        # Split the source into lines and process each individually
        for line in source.split('\n'):
            # Only process non-empty lines
            if line.strip() and line not in seen_sources:
                seen_sources.add(line)
                unique_sources.append(line)
    
    # Join the deduplicated sources
    all_sources = "\n".join(unique_sources)
    state.running_summary = f"## Summary\n\n{state.running_summary}\n\n ### Sources:\n{all_sources}"
    return {"running_summary": state.running_summary}

def route_research(state: SummaryState, config: RunnableConfig) -> Literal["finalize_summary", "web_research"]:
    """ Route the research based on the follow-up query """

    configurable = Configuration.from_runnable_config(config)
    if state.research_loop_count <= configurable.max_web_research_loops:
        return "web_research"
    else:
        return "finalize_summary"

# Add nodes and edges
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput, config_schema=Configuration)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

# Add edges
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", "summarize_sources")
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)
builder.add_edge("finalize_summary", END)

graph = builder.compile()