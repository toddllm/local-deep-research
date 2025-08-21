# Known Issues with Local Deep Researcher

## Critical Issues

### 1. Poor Search Results
- DuckDuckGo often returns irrelevant results (charity pages, dictionaries)
- Search queries are not specific enough
- No filtering of obviously irrelevant domains

### 2. Source Validation Not Enforcing Quality
- The `validate_sources` node correctly identifies bad sources
- But it doesn't filter them out or prevent their use
- Continues to summarize even with 0% relevant sources

### 3. LLM Hallucination with Bad Sources
- Model generates fake content when sources are irrelevant
- Mixes real concepts with unrelated source content
- Creates false statistics and claims

## Recommended Fixes

### Immediate:
1. **Enhance validate_sources to filter**:
   - Return filtered sources only
   - Trigger new search if all sources fail
   - Set minimum relevance threshold

2. **Improve Search**:
   - Use more specific search queries
   - Add domain filtering (exclude dictionaries, general news)
   - Try alternative search APIs (Tavily, SearXNG)

3. **Add Hallucination Prevention**:
   - Don't summarize if sources are irrelevant
   - Return "insufficient sources" message
   - Request user to refine query

### Long-term:
1. Switch to better search APIs (Tavily, Perplexity)
2. Implement source scoring and ranking
3. Add domain allowlists for technical topics
4. Use specialized models for research tasks