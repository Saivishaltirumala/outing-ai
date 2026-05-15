# OutingAI - Corporate Day Outing Planner

> Tell us your office location, team size, and budget - we'll suggest the best 3 spots for lunch or an activity today.

A LangGraph-based AI agent that connects to 3 MCP servers in real time to recommend the top lunch spots or team activity venues - scored by distance, rating, budget fit, and weather suitability.

## Architecture

```
React UI --> FastAPI --> LangGraph Agent
                            |
                   +--------+---------+
                   |        |         |
              Weather   Google Maps  Tavily
              MCP       MCP         Search MCP
                   |        |         |
                   v        v         v
             Is weather  Nearby     Recent
             okay for    restaurants reviews &
             outdoor?    & venues    tips
                   |        |         |
                   +--------+---------+
                            |
                            v
                 Top 3 Suggestions with
                 scores, distance, cost
                 estimate & why chosen

LLM: Claude (paid) / Groq (free) / Gemini (free)
```

## MCP Server Tools

### Google Maps MCP (`@modelcontextprotocol/server-google-maps`)

| Tool | Used In | Purpose |
|---|---|---|
| `maps_geocode` | `geocode_node` | Converts location name to lat/lng coordinates (e.g. "Hitech City, Hyderabad" -> 17.44, 78.38) |
| `maps_search_places` | `lunch_search_node`, `activity_search_node` | Finds nearby restaurants/activities within a radius with ratings, reviews, distance, and address |

### Weather MCP (`@dangahagan/weather-mcp`)

| Tool | Used In | Purpose |
|---|---|---|
| `get_forecast` | `weather_node` | Gets weather forecast at lat/lng to decide outdoor vs indoor suggestions |
| `get_current_conditions` | Available, not used | More detailed current weather conditions |
| `get_alerts` | Available, not used | Severe weather warnings/alerts |
| `search_location` | Available, not used | Search for a location by name |
| `check_service_status` | Available, not used | Check if the weather service is operational |

### Tavily Search MCP (`tavily-mcp`)

| Tool | Used In | Purpose |
|---|---|---|
| `tavily_search` | `lunch_search_node`, `activity_search_node` | Searches the web for blog reviews, hidden gems, and recent tips (e.g. "best team lunch spots Hitech City 2026") |

### MCP Configuration (`mcp_config.json`)

```json
{
  "mcpServers": {
    "tavily-search": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": { "TAVILY_API_KEY": "${TAVILY_API_KEY}" }
    },
    "google-maps": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-google-maps"],
      "env": { "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}" }
    },
    "weather": {
      "command": "npx",
      "args": ["-y", "@dangahagan/weather-mcp"]
    }
  }
}
```

### Which Node Uses Which Tools

```
geocode_node         -> Google Maps MCP only
                         maps_geocode

weather_node         -> Weather MCP only
                         get_forecast

lunch_search_node    -> Google Maps MCP + Tavily MCP
                         maps_search_places (structured data)
                         tavily_search (blog reviews)

activity_search_node -> Google Maps MCP + Tavily MCP
                         maps_search_places (structured data)
                         tavily_search (blog reviews)

score_lunch_node     -> NO MCP tools, only LLM
score_activity_node  -> NO MCP tools, only LLM
plan_both_node       -> NO MCP tools, only LLM
```

## LangGraph Flow

```
                    geocode
                       |
                  fetch_weather
                       |
            _route_by_type(state)
           /           |           \
     "lunch"      "activity"      "both"
         |             |              |
   lunch_search  activity_search  parallel_lunch_search
         |             |              |
   score_lunch   score_activity   parallel_activity_search
         |             |              |
        END           END         plan_both
                                      |
                                     END
```

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | User interface |
| Backend | Python + FastAPI | API server |
| Agent | LangGraph | State machine orchestration |
| LLM | Claude / Groq / Gemini (via LangChain) | Scoring and ranking |
| MCP Client | Python MCP SDK + langchain-mcp-adapters | Connects to MCP servers |
| MCP Servers | Node.js (via npx) | Weather, Maps, Search |
| Deployment | Docker + HuggingFace Spaces | Free hosting |

## API Keys Required

| Key | Provider | Free? | Required For |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic | Paid | Claude LLM (optional) |
| `GROQ_API_KEY` | Groq | Yes (14K req/day) | Groq/Llama LLM |
| `GOOGLE_API_KEY` | Google AI Studio | Yes (1.5K req/day) | Gemini LLM |
| `TAVILY_API_KEY` | Tavily | Yes (1K req/month) | Search MCP |
| `GOOGLE_MAPS_API_KEY` | Google Cloud | Yes ($200 free credit) | Maps MCP |
| Weather | Open-Meteo | Yes (no key needed) | Weather MCP |

## Setup

```bash
# Clone and enter project
cd 8-outing-ai

# Create .env with your API keys
cp .env.example .env

# Python backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# React frontend
cd frontend
npm install
npm run build
cd ..

# Run
python main.py
# Open http://localhost:7860
```

## Project Structure

```
8-outing-ai/
├── agent/
│   ├── graph.py          # LangGraph state machine
│   ├── nodes.py          # Each step (geocode, weather, search, score)
│   ├── state.py          # Shared state schema
│   ├── llm.py            # Multi-provider LLM factory
│   └── prompts.py        # LLM prompt templates
├── mcp_client/
│   └── client.py         # Spawns MCP servers, discovers tools
├── api/
│   └── routes.py         # FastAPI endpoint
├── models/
│   └── schemas.py        # Pydantic input/output models
├── frontend/
│   └── src/
│       ├── App.tsx        # Main React component
│       ├── api.ts         # API client
│       └── components/
│           ├── InputForm.tsx
│           └── Results.tsx
├── mcp_config.json       # MCP server declarations
├── Dockerfile            # HuggingFace Spaces deployment
├── .env                  # API keys (not committed)
└── requirements.txt
```

## Scoring Logic

```
Score = Distance from office   (25%) - closer is better
      + Rating                 (30%) - higher is better
      + Budget Fit             (25%) - within per-head limit
      + Weather Suitability    (20%) - outdoor needs good weather
```

## Deployment

Deploy to HuggingFace Spaces (free, Docker-based):

```bash
docker build -t outing-ai .
docker run -p 7860:7860 --env-file .env outing-ai
```

Set environment variables (API keys) as Secrets in HuggingFace Space settings.
