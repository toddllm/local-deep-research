# Research Rabbit 🐰

A fully local web research and summarization agent that autonomously explores topics in depth through iterative research cycles.

## 🚀 Quickstart with LangGraph server, Ollama and Tavily

Pull a local LLM that you want to use from [Ollama](https://ollama.com/search):
```bash
ollama pull llama3.1
```

Install the langgraph CLI:
```bash
pip install -U "langgraph-cli[inmem]"
```

Install dependencies:
```bash
pip install -e .
```

Load API keys into the environment for web search:
```bash
export TAVILY_API_KEY=<your_tavily_api_key>
```

Launch the agent:
```bash
langgraph dev
```

If all is well, you should see the following output:
> Ready!
> 
> API: http://127.0.0.1:2024
> 
> Docs: http://127.0.0.1:2024/docs
> 
> LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

Open `LangGraph Studio Web UI` via the URL in the output. 

In the `configuration` tab:
* You can set the name of your local LLM (it will by default be `llama3.1`) 
* You can set the depth of the research iterations (it will by default be `3`)

![Screenshot 2024-12-05 at 3 23 46 PM](https://github.com/user-attachments/assets/3c328426-b107-4ed5-82a5-625193f18435)

Give the agent a topic for research, and you can visualize its process.

![Screenshot 2024-12-05 at 2 58 26 PM](https://github.com/user-attachments/assets/a409203b-60b7-41ee-9a6a-7defb3d520a7)

## How it works

Research Rabbit is a AI-powered research assistant that:
- Given a user-provided topic, uses a local LLM (configured for [Ollama](https://ollama.com/search)) to generate a targeted web search query
- Uses a search engine (configured for [Tavily](https://www.tavily.com/)) to find relevant sources
- Uses a local LLM to summarizing the findings from web search related to the user-provided research topic
- Then, used the local LLM to reflect on the summary, identifying knowledge gaps and generating a new search query to explore the gaps
- The process repeats, with the summary being iteratively updated with new information from web search
- It will repeat down the research rabbit hole for a configurable number of iterations (configured in the `configuration` tab)  

## Outputs

The output of the graph is a markdown file containing the research summary, with citations to the sources used.

All sources gathered during research are saved to the graph state. 

You can visualize them in the graph state, which is visible in LangGraph Studio:

The final summary is saved to the graph state as well: 

