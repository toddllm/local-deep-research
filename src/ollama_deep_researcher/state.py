import operator
from dataclasses import dataclass, field
from typing_extensions import Annotated


@dataclass(kw_only=True)
class SummaryState:
    research_topic: str = field(default=None)  # Report topic
    search_query: str = field(default=None)  # Search query
    web_research_results: Annotated[list, operator.add] = field(default_factory=list)
    sources_gathered: Annotated[list, operator.add] = field(default_factory=list)
    research_loop_count: int = field(default=0)  # Research loop count
    running_summary: str = field(default=None)  # Final report
    validated_sources: bool = field(default=False)  # Source validation flag
    validation_retry_needed: bool = field(default=False)  # Need to retry search
    validation_retries: int = field(default=0)  # Number of validation retries
    validation_failed: bool = field(default=False)  # Validation completely failed
    seen_urls: set = field(default_factory=set)  # Track URLs across research loops
    query_history: Annotated[list, operator.add] = field(default_factory=list)  # Previous queries for refinement


@dataclass(kw_only=True)
class SummaryStateInput:
    research_topic: str = field(default=None)  # Report topic


@dataclass(kw_only=True)
class SummaryStateOutput:
    running_summary: str = field(default=None)  # Final report
