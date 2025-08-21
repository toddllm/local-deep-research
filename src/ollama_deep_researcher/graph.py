import json

from pydantic import BaseModel, Field
from typing_extensions import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph

from ollama_deep_researcher.configuration import Configuration, SearchAPI
from ollama_deep_researcher.utils import (
    deduplicate_and_format_sources,
    tavily_search,
    format_sources,
    perplexity_search,
    duckduckgo_search,
    searxng_search,
    arxiv_search,
    strip_thinking_tokens,
    get_config_value,
)
from ollama_deep_researcher.state import (
    SummaryState,
    SummaryStateInput,
    SummaryStateOutput,
)
from ollama_deep_researcher.prompts import (
    query_writer_instructions,
    summarizer_instructions,
    reflection_instructions,
    get_current_date,
    json_mode_query_instructions,
    tool_calling_query_instructions,
    json_mode_reflection_instructions,
    tool_calling_reflection_instructions,
)
from ollama_deep_researcher.lmstudio import ChatLMStudio

# Constants
MAX_TOKENS_PER_SOURCE = 1000
CHARS_PER_TOKEN = 4

def generate_search_query_with_structured_output(
    configurable: Configuration,
    messages: list,
    tool_class,
    fallback_query: str,
    tool_query_field: str,
    json_query_field: str,
    query_model: str = None,
):
    """Helper function to generate search queries using either tool calling or JSON mode.
    
    Args:
        configurable: Configuration object
        messages: List of messages to send to LLM
        tool_class: Tool class for tool calling mode
        fallback_query: Fallback search query if extraction fails
        tool_query_field: Field name in tool args containing the query
        json_query_field: Field name in JSON response containing the query
        
    Returns:
        Dictionary with "search_query" key
    """
    if configurable.use_tool_calling:
        llm = get_llm(configurable, query_model).bind_tools([tool_class])
        result = llm.invoke(messages)

        if not result.tool_calls:
            return {"search_query": fallback_query}
        
        try:
            tool_data = result.tool_calls[0]["args"]
            search_query = tool_data.get(tool_query_field)
            return {"search_query": search_query}
        except (IndexError, KeyError):
            return {"search_query": fallback_query}
    
    else:
        # Use JSON mode
        llm = get_llm(configurable, query_model)
        result = llm.invoke(messages)
        print(f"result: {result}")
        content = result.content

        try:
            parsed_json = json.loads(content)
            search_query = parsed_json.get(json_query_field)
            if not search_query:
                return {"search_query": fallback_query}
            return {"search_query": search_query}
        except (json.JSONDecodeError, KeyError):
            if configurable.strip_thinking_tokens:
                content = strip_thinking_tokens(content)
            return {"search_query": fallback_query}

def get_llm(configurable: Configuration, model_override: str = None):
    """Helper function to initialize LLM based on configuration.

    Uses JSON mode if use_tool_calling is False, otherwise regular mode for tool calling.

    Args:
        configurable: Configuration object containing LLM settings
        model_override: Optional model name to override the default

    Returns:
        Configured LLM instance
    """
    model = model_override or configurable.local_llm
    
    if configurable.llm_provider == "lmstudio":
        if configurable.use_tool_calling:
            return ChatLMStudio(
                base_url=configurable.lmstudio_base_url,
                model=model,
                temperature=0,
            )
        else:
            return ChatLMStudio(
                base_url=configurable.lmstudio_base_url,
                model=model,
                temperature=0,
                format="json",
            )
    else:  # Default to Ollama
        if configurable.use_tool_calling:
            return ChatOllama(
                base_url=configurable.ollama_base_url,
                model=model,
                temperature=0,
            )
        else:
            return ChatOllama(
                base_url=configurable.ollama_base_url,
                model=model,
                temperature=0,
                format="json",
            )

# Nodes
def generate_query(state: SummaryState, config: RunnableConfig):
    """LangGraph node that generates a search query based on the research topic.

    Uses an LLM to create an optimized search query for web research based on
    the user's research topic. Supports both LMStudio and Ollama as LLM providers.

    Args:
        state: Current graph state containing the research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """

    # Get progress callback if available
    progress_callback = config.get("configurable", {}).get("progress_callback", lambda x, y=None, z=None: None)
    
    # Format the prompt
    current_date = get_current_date()
    
    # Add query history context if available
    query_history_context = ""
    if state.query_history and len(state.query_history) > 0:
        query_history_context = f"\n\n<PREVIOUS_QUERIES>\nPrevious search queries used in this research:\n"
        for i, prev_query in enumerate(state.query_history, 1):
            query_history_context += f"{i}. {prev_query}\n"
        query_history_context += "\nGenerate a NEW, different query that explores unexplored aspects or addresses knowledge gaps not covered by previous searches.\n</PREVIOUS_QUERIES>"
    
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date, research_topic=state.research_topic
    ) + query_history_context

    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    
    progress_callback(
        "🧠 Analyzing research topic",
        f"Topic: {state.research_topic}",
        {"stage": "query_generation", "topic": state.research_topic}
    )

    @tool
    class Query(BaseModel):
        """
        This tool is used to generate a query for web search.
        """

        query: str = Field(description="The actual search query string")
        rationale: str = Field(
            description="Brief explanation of why this query is relevant"
        )

    messages = [
        SystemMessage(
            content=formatted_prompt + (
                tool_calling_query_instructions if configurable.use_tool_calling 
                else json_mode_query_instructions
            )
        ),
        HumanMessage(content="Generate a query for web search:"),
    ]

    # Check for custom query model
    query_model = config.get("configurable", {}).get("query_model")
    
    result = generate_search_query_with_structured_output(
        configurable=configurable,
        messages=messages,
        tool_class=Query,
        fallback_query=f"Tell me more about {state.research_topic}",
        tool_query_field="query",
        json_query_field="query",
        query_model=query_model,
    )
    
    # Add generated query to history for future reference
    if "search_query" in result:
        result["query_history"] = [result["search_query"]]
    
    return result


def web_research(state: SummaryState, config: RunnableConfig):
    """LangGraph node that performs web research using the generated search query.

    Executes a web search using the configured search API (tavily, perplexity,
    duckduckgo, or searxng) and formats the results for further processing.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """

    # Configure
    configurable = Configuration.from_runnable_config(config)
    
    # Get progress callback if available
    progress_callback = config.get("configurable", {}).get("progress_callback", None)
    if not progress_callback:
        progress_callback = lambda x, y=None, z=None: None
    
    # Fix: don't add 1 to loop count since it starts at 1
    current_loop = state.research_loop_count
    if current_loop == 0:
        current_loop = 1
    
    # Check if we have multiple search APIs to aggregate
    search_apis = config.get("configurable", {}).get("search_apis", None)
    
    if search_apis and isinstance(search_apis, list) and len(search_apis) > 0:
        # Multi-source search aggregation
        progress_callback(
            f"🔍 Aggregating results from {len(search_apis)} sources (Loop {current_loop}/{configurable.max_web_research_loops})",
            f"Query: {state.search_query}",
            {"sources": search_apis, "loop": current_loop}
        )
        
        all_search_results = []
        all_formatted_sources = []
        
        for api in search_apis:
            progress_callback(
                f"📡 Searching {api}...",
                f"Query: {state.search_query}",
                {"api": api, "loop": current_loop}
            )
            
            try:
                if api == "tavily":
                    results = tavily_search(
                        state.search_query,
                        fetch_full_page=configurable.fetch_full_page,
                        max_results=2,  # Fewer results per source when aggregating
                    )
                elif api == "perplexity":
                    results = perplexity_search(
                        state.search_query, state.research_loop_count
                    )
                elif api == "duckduckgo":
                    results = duckduckgo_search(
                        state.search_query,
                        max_results=2,
                        fetch_full_page=configurable.fetch_full_page,
                    )
                elif api == "searxng":
                    results = searxng_search(
                        state.search_query,
                        max_results=2,
                        fetch_full_page=configurable.fetch_full_page,
                    )
                elif api == "arxiv":
                    results = arxiv_search(
                        state.search_query,
                        max_results=2,
                        fetch_full_page=configurable.fetch_full_page,
                    )
                else:
                    progress_callback(
                        f"⚠️ Skipping unsupported API: {api}",
                        None,
                        {"api": api, "error": "Unsupported"}
                    )
                    continue
                
                if results and "results" in results and len(results["results"]) > 0:
                    all_search_results.append(results)
                    all_formatted_sources.append(format_sources(results))
                    progress_callback(
                        f"✅ Found {len(results['results'])} results from {api}",
                        f"Sources: {', '.join(r['title'][:50] for r in results['results'][:2])}",
                        {"api": api, "count": len(results["results"]), "results": results["results"]}
                    )
                else:
                    progress_callback(
                        f"⚠️ No results from {api}",
                        None,
                        {"api": api, "count": 0}
                    )
                    
            except Exception as e:
                progress_callback(
                    f"❌ Error searching {api}: {str(e)}",
                    str(e),
                    {"api": api, "error": str(e)}
                )
        
        # Deduplicate and format all aggregated results
        if all_search_results:
            search_str = deduplicate_and_format_sources(
                all_search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
            
            # Update seen URLs with new URLs from this search
            for result_set in all_search_results:
                if "results" in result_set:
                    for result in result_set["results"]:
                        if "url" in result:
                            state.seen_urls.add(result["url"])
            formatted_sources = "\n".join(all_formatted_sources)
            
            total_results = sum(len(r.get('results', [])) for r in all_search_results)
            progress_callback(
                f"🎯 Aggregation complete: {total_results} total results from {len(all_search_results)} sources",
                f"Successfully searched: {len([s for s in all_formatted_sources if s])} APIs",
                {"total_sources": len(all_search_results), "total_results": total_results}
            )
        else:
            search_str = "No search results found."
            formatted_sources = ""
            progress_callback(
                "⚠️ No results from any search source",
                "All search attempts failed or returned no results",
                {"total_sources": 0, "total_results": 0}
            )
        
        return {
            "sources_gathered": [formatted_sources],
            "research_loop_count": state.research_loop_count + 1,
            "web_research_results": [search_str],
        }
    else:
        # Single search API (original behavior)
        progress_callback(
            f"🔍 Searching web (Loop {current_loop}/{configurable.max_web_research_loops})",
            f"Query: {state.search_query} | API: {configurable.search_api}",
            {"api": configurable.search_api, "loop": current_loop}
        )

        # Get the search API
        search_api = get_config_value(configurable.search_api)

        # Search the web
        if search_api == "tavily":
            search_results = tavily_search(
                state.search_query,
                fetch_full_page=configurable.fetch_full_page,
                max_results=1,
            )
            search_str = deduplicate_and_format_sources(
                search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
        elif search_api == "perplexity":
            search_results = perplexity_search(
                state.search_query, state.research_loop_count
            )
            search_str = deduplicate_and_format_sources(
                search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
        elif search_api == "duckduckgo":
            search_results = duckduckgo_search(
                state.search_query,
                max_results=3,
                fetch_full_page=configurable.fetch_full_page,
            )
            search_str = deduplicate_and_format_sources(
                search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
        elif search_api == "searxng":
            search_results = searxng_search(
                state.search_query,
                max_results=3,
                fetch_full_page=configurable.fetch_full_page,
            )
            search_str = deduplicate_and_format_sources(
                search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
        elif search_api == "arxiv":
            search_results = arxiv_search(
                state.search_query,
                max_results=3,
                fetch_full_page=configurable.fetch_full_page,
            )
            search_str = deduplicate_and_format_sources(
                search_results,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
                fetch_full_page=configurable.fetch_full_page,
                seen_urls=state.seen_urls,
            )
        else:
            raise ValueError(f"Unsupported search API: {configurable.search_api}")

        # Update seen URLs with new URLs from this single search
        if search_results and "results" in search_results:
            for result in search_results["results"]:
                if "url" in result:
                    state.seen_urls.add(result["url"])

        return {
            "sources_gathered": [format_sources(search_results)],
            "research_loop_count": state.research_loop_count + 1,
            "web_research_results": [search_str],
        }


def validate_sources(state: SummaryState, config: RunnableConfig):
    """LangGraph node that validates the quality and relevance of web research sources.

    Analyzes the gathered sources to ensure they are relevant, credible, and provide
    substantive information related to the research topic. Filters out low-quality
    or irrelevant sources and can trigger new searches if needed.

    Args:
        state: Current graph state containing research topic and web research results
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including validated_sources flag and filtered results
    """
    
    # Get progress callback if available
    progress_callback = config.get("configurable", {}).get("progress_callback", lambda x, y=None, z=None: None)
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Get most recent web research and sources
    if not state.web_research_results:
        return {"validated_sources": False, "validation_retry_needed": False}
    
    most_recent_web_research = state.web_research_results[-1]
    most_recent_sources = state.sources_gathered[-1] if state.sources_gathered else ""
    
    # Check if we've already tried validating too many times
    current_retries = getattr(state, 'validation_retries', 0)
    
    progress_callback(
        "🔍 Analyzing source quality",
        f"Validating {len(most_recent_sources.split('* '))-1} sources for relevance",
        {"source_count": len(most_recent_sources.split('* '))-1, "retry_count": current_retries}
    )
    
    # Create structured validation prompt with enhanced academic paper evaluation
    validation_prompt = f"""
    Analyze these web search results for research on: {state.research_topic}
    
    Sources to evaluate:
    {most_recent_sources}
    
    For EACH source, provide a relevance score from 0.0 to 1.0 using these enhanced criteria:
    
    GENERAL SOURCES (0.0-1.0):
    - 0.0-0.3: Completely irrelevant (dictionaries, unrelated topics, spam)
    - 0.4-0.6: Somewhat relevant (general news, tangentially related content)
    - 0.7-0.9: Highly relevant (specific to topic, authoritative sources)
    - 1.0: Perfect match (expert source directly addressing the topic)
    
    ACADEMIC PAPERS (arXiv, journal articles):
    Apply additional evaluation criteria:
    - Title relevance: Does the paper title directly address the research topic?
    - Abstract quality: Does the abstract indicate the paper contains substantial relevant content?
    - Publication date: Recent papers (within 2-3 years) may be more valuable for emerging topics
    - Author credentials: Papers from established researchers or institutions get higher scores
    - Paper type: Original research papers score higher than surveys unless surveys are specifically needed
    - Technical depth: Papers with sufficient technical detail score higher than superficial treatments
    
    For academic papers, boost scores by 0.1-0.2 if they are:
    - Recent high-quality research directly on topic
    - From reputable institutions or well-cited authors
    - Contain novel findings or comprehensive analysis
    
    Return your evaluation in JSON format:
    {{
        "sources": [
            {{"url": "...", "title": "...", "relevance_score": 0.0, "reason": "...", "source_type": "academic/web/news"}},
        ],
        "overall_quality": "low/medium/high",
        "recommendation": "proceed/retry/refine_query",
        "academic_paper_count": 0,
        "high_quality_academic_sources": 0
    }}
    """
    
    # Initialize LLM for validation with JSON mode
    if configurable.llm_provider == "lmstudio":
        llm = ChatLMStudio(
            base_url=configurable.lmstudio_base_url,
            model=configurable.local_llm,
            temperature=0,
            format="json",
        )
    else:  # Default to Ollama
        llm = ChatOllama(
            base_url=configurable.ollama_base_url,
            model=configurable.local_llm,
            temperature=0,
            format="json",
        )
    
    # Run validation
    try:
        result = llm.invoke([
            SystemMessage(content="You are a research quality assessor. Evaluate source relevance and return JSON."),
            HumanMessage(content=validation_prompt)
        ])
        
        # Parse validation result
        validation_result = result.content
        if configurable.strip_thinking_tokens:
            validation_result = strip_thinking_tokens(validation_result)
        
        import json
        validation_data = json.loads(validation_result)
        
        # Check if sources meet minimum relevance score
        valid_sources = []
        for source_eval in validation_data.get("sources", []):
            score = source_eval.get("relevance_score", 0)
            if score >= configurable.min_source_relevance_score:
                valid_sources.append(source_eval)
                print(f"✅ Valid source (score: {score}): {source_eval.get('title', 'Unknown')}")
            else:
                print(f"❌ Filtered source (score: {score}): {source_eval.get('title', 'Unknown')} - {source_eval.get('reason', '')}")
        
        # Determine if we have enough valid sources
        has_valid_sources = len(valid_sources) > 0
        
        if not has_valid_sources and configurable.require_valid_sources:
            print(f"⚠️ No valid sources found. Minimum score required: {configurable.min_source_relevance_score}")
            
            # Check if we've exceeded retry limit - prevent infinite recursion
            if current_retries >= configurable.max_validation_retries:
                print(f"❌ Maximum validation retries ({configurable.max_validation_retries}) exceeded")
                # Don't retry anymore - just continue with what we have
                return {
                    "validated_sources": False,
                    "validation_failed": False,  # Don't fail completely, just continue
                    "validation_retry_needed": False,
                    "web_research_results": state.web_research_results  # Keep existing results
                }
            
            # Only retry if we haven't exceeded the limit
            print(f"🔄 Retrying search (attempt {current_retries + 1}/{configurable.max_validation_retries})")
            return {
                "validated_sources": False,
                "validation_retry_needed": True,
                "validation_retries": current_retries + 1,
                "search_query": f"{state.search_query} academic research scholarly"
            }
        
        # If we have valid sources, filter the results
        if has_valid_sources and len(valid_sources) < len(validation_data.get("sources", [])):
            # Filter the web research results to only include valid sources
            filtered_results = []
            for source_eval in valid_sources:
                # Extract the relevant portion from the original results
                url = source_eval.get("url", "")
                if url and url in most_recent_web_research:
                    # Find and extract this source's content
                    start_idx = most_recent_web_research.find(url)
                    if start_idx != -1:
                        # Find the next source or end
                        next_source_idx = most_recent_web_research.find("\n\nSource:", start_idx + 1)
                        if next_source_idx == -1:
                            source_content = most_recent_web_research[start_idx:]
                        else:
                            source_content = most_recent_web_research[start_idx:next_source_idx]
                        filtered_results.append(source_content)
            
            if filtered_results:
                filtered_web_research = "\n\n".join(filtered_results)
                return {
                    "validated_sources": True,
                    "web_research_results": [filtered_web_research] if filtered_web_research else state.web_research_results
                }
        
        return {"validated_sources": has_valid_sources}
        
    except Exception as e:
        print(f"Validation error: {e}")
        # Fallback to simple validation
        return {"validated_sources": True}


def summarize_sources(state: SummaryState, config: RunnableConfig):
    """LangGraph node that summarizes web research results.

    Uses an LLM to create or update a running summary based on the newest web research
    results, integrating them with any existing summary.

    Args:
        state: Current graph state containing research topic, running summary,
              and web research results
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including running_summary key containing the updated summary
    """
    
    # Get progress callback if available
    progress_callback = config.get("configurable", {}).get("progress_callback", lambda x, y=None, z=None: None)

    # Existing summary
    existing_summary = state.running_summary

    # Most recent web research
    most_recent_web_research = state.web_research_results[-1]

    # Build the human message
    if existing_summary:
        human_message_content = (
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Context> \n {most_recent_web_research} \n <New Context>"
            f"Update the Existing Summary with the New Context on this topic: \n <User Input> \n {state.research_topic} \n <User Input>\n\n"
        )
    else:
        human_message_content = (
            f"<Context> \n {most_recent_web_research} \n <Context>"
            f"Create a Summary using the Context on this topic: \n <User Input> \n {state.research_topic} \n <User Input>\n\n"
        )

    # Run the LLM
    configurable = Configuration.from_runnable_config(config)
    
    # Log summary generation
    if existing_summary:
        progress_callback(
            "📝 Updating existing summary with new research",
            f"Integrating {len(most_recent_web_research.split())} words of new content",
            {"existing_summary_length": len(existing_summary.split()), "new_content_length": len(most_recent_web_research.split())}
        )
    else:
        progress_callback(
            "📝 Creating initial research summary",
            f"Processing {len(most_recent_web_research.split())} words of research data",
            {"content_length": len(most_recent_web_research.split())}
        )

    # For summarization, we don't need structured output, so always use regular mode
    # Check if we have a separate summarization model configured
    summarization_model = config.get("configurable", {}).get("summarization_model", configurable.local_llm)
    
    if configurable.llm_provider == "lmstudio":
        llm = ChatLMStudio(
            base_url=configurable.lmstudio_base_url,
            model=summarization_model,
            temperature=0,
        )
    else:  # Default to Ollama
        llm = ChatOllama(
            base_url=configurable.ollama_base_url,
            model=summarization_model,
            temperature=0,
        )
    
    summarization_model = config.get("configurable", {}).get("summarization_model", configurable.local_llm)
    progress_callback(
        f"🤖 Invoking {summarization_model} for summarization",
        f"Using {configurable.llm_provider} provider",
        {"model": summarization_model, "provider": configurable.llm_provider}
    )

    result = llm.invoke(
        [
            SystemMessage(content=summarizer_instructions),
            HumanMessage(content=human_message_content),
        ]
    )

    # Strip thinking tokens if configured
    running_summary = result.content
    if configurable.strip_thinking_tokens:
        running_summary = strip_thinking_tokens(running_summary)
    
    progress_callback(
        "✅ Summary generation complete",
        f"Generated {len(running_summary.split())} word summary",
        {"summary_length": len(running_summary.split()), "stripped_thinking": configurable.strip_thinking_tokens}
    )

    return {"running_summary": running_summary}


def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """LangGraph node that identifies knowledge gaps and generates follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    a new search query to address those gaps. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """

    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = reflection_instructions.format(
        research_topic=state.research_topic
    )

    @tool
    class FollowUpQuery(BaseModel):
        """
        This tool is used to generate a follow-up query to address a knowledge gap.
        """

        follow_up_query: str = Field(
            description="Write a specific question to address this gap"
        )
        knowledge_gap: str = Field(
            description="Describe what information is missing or needs clarification"
        )

    messages = [
        SystemMessage(
            content=formatted_prompt + (
                tool_calling_reflection_instructions if configurable.use_tool_calling 
                else json_mode_reflection_instructions
            )
        ),
        HumanMessage(
            content=f"Reflect on our existing knowledge: \n === \n {state.running_summary}, \n === \n And now identify a knowledge gap and generate a follow-up web search query:"
        ),
    ]

    # Check for custom query model
    query_model = config.get("configurable", {}).get("query_model")
    
    return generate_search_query_with_structured_output(
        configurable=configurable,
        messages=messages,
        tool_class=FollowUpQuery,
        fallback_query=f"Tell me more about {state.research_topic}",
        tool_query_field="follow_up_query",
        json_query_field="follow_up_query",
        query_model=query_model,
    )


def finalize_summary(state: SummaryState):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """

    # Deduplicate sources before joining
    seen_sources = set()
    unique_sources = []

    for source in state.sources_gathered:
        # Split the source into lines and process each individually
        for line in source.split("\n"):
            # Only process non-empty lines
            if line.strip() and line not in seen_sources:
                seen_sources.add(line)
                # Convert "Title : URL" format to markdown link
                if " : " in line:
                    parts = line.split(" : ", 1)
                    if len(parts) == 2:
                        title, url = parts
                        # Remove bullet point if present
                        title = title.lstrip("* ").strip()
                        line = f"* [{title}]({url})"
                unique_sources.append(line)

    # Join the deduplicated sources
    all_sources = "\n".join(unique_sources)
    state.running_summary = (
        f"## Summary\n{state.running_summary}\n\n### Sources:\n{all_sources}"
    )
    return {"running_summary": state.running_summary}


def route_research(
    state: SummaryState, config: RunnableConfig
) -> Literal["finalize_summary", "web_research"]:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_web_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """

    configurable = Configuration.from_runnable_config(config)
    if state.research_loop_count <= configurable.max_web_research_loops:
        return "web_research"
    else:
        return "finalize_summary"


def route_validation(
    state: SummaryState, config: RunnableConfig
) -> Literal["summarize_sources", "web_research"]:
    """LangGraph routing function that routes based on validation results.

    Determines next step based on source validation results:
    - If retry needed AND under retry limit: go back to web_research
    - Otherwise: continue to summarize_sources

    Args:
        state: Current graph state containing validation results
        config: Configuration for the runnable

    Returns:
        String literal indicating the next node to visit
    """
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Check if we should retry
    if state.validation_retry_needed:
        current_retries = getattr(state, 'validation_retries', 0)
        if current_retries < configurable.max_validation_retries:
            return "web_research"
    
    # Default: continue to summarization
    return "summarize_sources"


# Add nodes and edges
builder = StateGraph(
    SummaryState,
    input=SummaryStateInput,
    output=SummaryStateOutput,
    config_schema=Configuration,
)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("validate_sources", validate_sources)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

# Add edges
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", "validate_sources")
# Conditional routing from validate_sources based on validation results
builder.add_conditional_edges("validate_sources", route_validation)
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)
builder.add_edge("finalize_summary", END)

graph = builder.compile()
