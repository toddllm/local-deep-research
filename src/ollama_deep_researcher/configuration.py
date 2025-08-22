import os
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal

from langchain_core.runnables import RunnableConfig


class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    SEARXNG = "searxng"
    ARXIV = "arxiv"


class Configuration(BaseModel):
    """The configurable fields for the research assistant."""

    max_web_research_loops: int = Field(
        default=3,
        title="Research Depth",
        description="Number of research iterations to perform",
    )
    local_llm: str = Field(
        default="llama3.2",
        title="LLM Model Name",
        description="Name of the LLM model to use",
    )
    llm_provider: Literal["ollama", "lmstudio"] = Field(
        default="ollama",
        title="LLM Provider",
        description="Provider for the LLM (Ollama or LMStudio)",
    )
    search_api: Literal["perplexity", "tavily", "duckduckgo", "searxng", "arxiv"] = Field(
        default="tavily", title="Search API", description="Web search API to use (tavily recommended)"
    )
    fetch_full_page: bool = Field(
        default=False,
        title="Fetch Full Page",
        description="Include the full page content in the search results",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434/",
        title="Ollama Base URL",
        description="Base URL for Ollama API",
    )
    lmstudio_base_url: str = Field(
        default="http://localhost:1234/v1",
        title="LMStudio Base URL",
        description="Base URL for LMStudio OpenAI-compatible API",
    )
    strip_thinking_tokens: bool = Field(
        default=True,
        title="Strip Thinking Tokens",
        description="Whether to strip <think> tokens from model responses",
    )
    use_tool_calling: bool = Field(
        default=False,
        title="Use Tool Calling",
        description="Use tool calling instead of JSON mode for structured output",
    )
    min_source_relevance_score: float = Field(
        default=0.5,
        title="Minimum Source Relevance Score",
        description="Minimum relevance score (0-1) to accept a source",
    )
    require_valid_sources: bool = Field(
        default=True,
        title="Require Valid Sources",
        description="Retry search if no valid sources found",
    )
    max_validation_retries: int = Field(
        default=1,
        title="Maximum Validation Retries",
        description="Maximum number of search retries when sources fail validation",
    )
    enable_memory_monitoring: bool = Field(
        default=True,
        title="Enable Memory Monitoring",
        description="Monitor memory usage during research",
    )
    memory_limit_mb: Optional[int] = Field(
        default=None,
        title="Memory Limit (MB)",
        description="Optional memory limit in MB (None for no limit)",
    )
    optimize_for_low_memory: bool = Field(
        default=False,
        title="Optimize for Low Memory",
        description="Use memory-efficient settings for resource-constrained environments",
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from config first, then environment as fallback
        raw_values: dict[str, Any] = {
            name: configurable.get(name, os.environ.get(name.upper()))
            for name in cls.model_fields.keys()
        }

        # Filter out None and empty string values to ensure proper fallbacks
        values = {k: v for k, v in raw_values.items() if v is not None and v != ""}
        
        # Validate that we don't have placeholder values - fail loudly if we do
        if values.get('local_llm') == 'your_model_name':
            raise ValueError("LOCAL_LLM is set to placeholder value 'your_model_name'. Please configure a real model name.")

        return cls(**values)
