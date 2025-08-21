# Setting Up Tavily for Better Search Results

## Why Tavily?

DuckDuckGo often returns irrelevant results (charity pages, dictionary definitions, etc.) for technical research topics. Tavily provides:
- Higher quality, research-focused search results
- Better relevance for technical and academic topics
- Structured data with content snippets
- Free tier with 100 searches/month

## Quick Setup

### 1. Get Your Free Tavily API Key

1. Go to [https://tavily.com](https://tavily.com)
2. Click "Sign Up" or "Get Started"
3. Create a free account
4. Navigate to your API Keys section
5. Copy your API key (starts with `tvly-`)

### 2. Configure Your Environment

Edit your `.env` file:

```bash
# Replace with your actual Tavily API key
TAVILY_API_KEY=tvly-YOUR_ACTUAL_KEY_HERE

# Ensure Tavily is selected as search API
SEARCH_API=tavily
```

### 3. Verify Setup

Run a test search:

```python
python -c "
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
results = client.search('quantum computing 2024')
print(f'✅ Tavily working! Found {len(results['results'])} results')
"
```

## Troubleshooting

### "Invalid API Key" Error
- Verify your key starts with `tvly-`
- Check for extra spaces or quotes in .env file
- Ensure you've activated your account via email

### No Results Returned
- Check your API usage limits (100/month for free tier)
- Try a simpler search query
- Verify internet connection

### Fallback to DuckDuckGo
If Tavily fails, the system will automatically fall back to DuckDuckGo. To force DuckDuckGo:

```bash
SEARCH_API=duckduckgo
# No API key needed for DuckDuckGo
```

## Enhanced Source Validation

With the new validation system:
- Sources scoring below 0.5 relevance are automatically filtered
- System retries with refined queries if no valid sources found
- Maximum 2 retries before giving up
- Configure thresholds in .env:

```bash
MIN_SOURCE_RELEVANCE_SCORE=0.5  # Adjust threshold (0-1)
REQUIRE_VALID_SOURCES=true      # Enable/disable retry on bad sources
```

## API Limits

| Plan | Searches/Month | Cost |
|------|---------------|------|
| Free | 100 | $0 |
| Researcher | 1,000 | $10 |
| Pro | 10,000 | $70 |

## Alternative Search APIs

If Tavily doesn't meet your needs:

### Perplexity API
```bash
SEARCH_API=perplexity
PERPLEXITY_API_KEY=pplx-YOUR_KEY_HERE
```

### SearXNG (Self-hosted)
```bash
SEARCH_API=searxng
SEARXNG_URL=http://localhost:8888
```

## Testing the Improved System

After setup, test with:
```bash
python run_research.py
```

You should see:
- ✅ Valid sources being accepted
- ❌ Irrelevant sources being filtered
- Automatic retries if all sources fail validation
- Higher quality final summaries