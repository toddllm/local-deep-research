from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """Your goal is to generate a highly targeted, specific web search query that will yield high-quality results.

<CONTEXT>
Current date: {current_date}
Please ensure your queries account for the most current information available as of this date.
</CONTEXT>

<TOPIC>
{research_topic}
</TOPIC>

<QUERY_OPTIMIZATION_GUIDELINES>
1. AVOID generic patterns like "Tell me more about..." or "What is..."
2. Use specific terminology and technical language when appropriate
3. Include relevant time constraints (e.g., "2024", "latest", "recent developments")
4. Consider the topic domain and use field-specific keywords
5. Focus on actionable, specific aspects rather than broad overviews
6. Include measurement terms when relevant (performance, metrics, benchmarks)
7. Use quotation marks for exact phrases when beneficial
8. Consider different perspectives (technical, business, academic, practical)
</QUERY_OPTIMIZATION_GUIDELINES>

<DOMAIN_SPECIFIC_STRATEGIES>
- Technology/Software: Include version numbers, frameworks, implementation details
- Science/Research: Include methodology, recent studies, peer-reviewed sources
- Business/Finance: Include market data, trends, financial metrics, case studies
- Medical/Health: Include clinical trials, evidence-based practices, recent guidelines
- Academic: Include author names, institution affiliations, publication dates
</DOMAIN_SPECIFIC_STRATEGIES>

<EXAMPLE>
Topic: "machine learning transformer architecture"
Poor query: "what is transformer architecture"
Good query: "transformer neural network architecture attention mechanism implementation 2024"
Rationale: "Specific technical terms, includes recent developments, focuses on implementation details"
</EXAMPLE>"""

json_mode_query_instructions = """<FORMAT>
You MUST respond with valid JSON format only. Do not include any text before or after the JSON object.

Format your response as a JSON object with these exact keys:
- "query": The actual search query string
- "rationale": Brief explanation of why this query is relevant

Example: {"query": "machine learning transformer architecture 2024", "rationale": "Targets recent developments in transformer models"}
</FORMAT>

Provide your response in JSON format:"""

tool_calling_query_instructions = """<INSTRUCTIONS   >
Call the Query tool to format your response with the following keys:
   - "query": The actual search query string
   - "rationale": Brief explanation of why this query is relevant
</INSTRUCTIONS>

Call the Query Tool to generate a query for this request:"""

summarizer_instructions = """
<GOAL>
Generate a high-quality summary of the provided context.
</GOAL>

<REQUIREMENTS>
When creating a NEW summary:
1. Highlight the most relevant information related to the user topic from the search results
2. Ensure a coherent flow of information

When EXTENDING an existing summary:                                                                                                                 
1. Read the existing summary and new search results carefully.                                                    
2. Compare the new information with the existing summary.                                                         
3. For each piece of new information:                                                                             
    a. If it's related to existing points, integrate it into the relevant paragraph.                               
    b. If it's entirely new but relevant, add a new paragraph with a smooth transition.                            
    c. If it's not relevant to the user topic, skip it.                                                            
4. Ensure all additions are relevant to the user's topic.                                                         
5. Verify that your final output differs from the input summary.                                                                                                                                                            
< /REQUIREMENTS >

< FORMATTING >
- Start directly with the updated summary, without preamble or titles. Do not use XML tags in the output.  
< /FORMATTING >

<Task>
Think carefully about the provided Context first. Then generate a summary of the context to address the User Input.
</Task>
"""

reflection_instructions = """You are an expert research assistant analyzing a summary about {research_topic}.

<GOAL>
1. Identify knowledge gaps or areas that need deeper exploration
2. Generate a follow-up question that would help expand your understanding
3. Focus on technical details, implementation specifics, or emerging trends that weren't fully covered
</GOAL>

<REQUIREMENTS>
Ensure the follow-up question is self-contained and includes necessary context for web search.
</REQUIREMENTS>"""

json_mode_reflection_instructions = """<FORMAT>
Format your response as a JSON object with these exact keys:
- knowledge_gap: Describe what information is missing or needs clarification
- follow_up_query: Write a specific question to address this gap
</FORMAT>

<Task>
Reflect carefully on the Summary to identify knowledge gaps and produce a follow-up query. Then, produce your output following this JSON format:
{{
    "knowledge_gap": "The summary lacks information about performance metrics and benchmarks",
    "follow_up_query": "What are typical performance benchmarks and metrics used to evaluate [specific technology]?"
}}
</Task>

Provide your analysis in JSON format:"""

tool_calling_reflection_instructions = """<INSTRUCTIONS>
Call the FollowUpQuery tool to format your response with the following keys:
- follow_up_query: Write a specific question to address this gap
- knowledge_gap: Describe what information is missing or needs clarification
</INSTRUCTIONS>

<Task>
Reflect carefully on the Summary to identify knowledge gaps and produce a follow-up query.
</Task>

Call the FollowUpQuery Tool to generate a reflection for this request:"""