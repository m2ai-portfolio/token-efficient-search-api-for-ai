
<p align="center">
  <img src="assets/infographic.png" alt="Token-Efficient Search API for AI" width="800">
</p>

<h3 align="center">A web search API optimized for AI agents that returns the most relevant documents while minimizing token usage.</h3>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#examples">Examples</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

## What is this?
Token-Efficient Search API for AI provides developers with a specialized search service that delivers concise, relevant web results optimized for language model consumption. It strips unnecessary HTML, ads, and boilerplate while preserving core informational content to maximize token efficiency within AI agent context windows.

Example usage:
```
$ token-efficient-search --query "renewable energy storage innovations" --limit 400
{
  "query": "renewable energy storage innovations",
  "results": [
    {
      "title": "Breakthroughs in Grid-Scale Battery Technology",
      "content": "Lithium-ion alternatives like flow batteries are enabling longer duration storage for renewable integration...",
      "tokens": 210
    },
    {
      "title": "Hydrogen Storage Solutions for Renewable Energy",
      "content": "Green hydrogen production coupled with salt cavern storage offers seasonal balancing capabilities...",
      "tokens": 185
    }
  ],
  "tokens_used": 395,
  "tokens_available": 5
}
```

## Problem
AI agents need to search the web, but standard search APIs return bloated results that waste tokens and context windows. Every unnecessary token increases API costs and reduces the information agents can process. Developers building AI agents need search infrastructure specifically optimized for token efficiency and relevance.

## Features
| Feature                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| Semantic Content Extraction      | Removes HTML markup, ads, navigation, and boilerplate while preserving core informational sentences and structural elements like headings in plain text. |
| Token Budget Optimization        | Dynamically truncates responses to fit specified token limits using relevance-based prioritization and accurate model-specific token counting via tiktoken. |
| Multi-Source Relevance Scoring   | Combines results from Google and Bing APIs, ranks content using semantic similarity embeddings, and deduplicates similar information across sources. |
| Configurable Response Formats    | Supports optimization strategies including comprehensive, concise, and bullet-point output to match different AI agent processing requirements. |

## Quick Start
1. Clone the repository:
   ```
   git clone https://github.com/m2ai-portfolio/token-efficient-search-api.git
   cd token-efficient-search-api
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure required environment variables:
   ```
   export GOOGLE_SEARCH_API_KEY="your_google_api_key"
   export GOOGLE_SEARCH_ENGINE_ID="your_search_engine_id"
   export REDIS_URL="redis://localhost:6379"  # Default if Redis runs locally
   ```

4. Start the API server:
   ```
   uvicorn src.core:app --reload