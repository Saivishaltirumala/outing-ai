from __future__ import annotations

import time
import functools
from contextlib import AsyncExitStack

from langgraph.graph import StateGraph, END
from langchain_core.tools import BaseTool

from agent.state import OutingState
from agent.nodes import (
    geocode_node,
    weather_node,
    lunch_search_node,
    activity_search_node,
    score_lunch_node,
    score_activity_node,
    plan_both_node,
)
from mcp_client.client import create_mcp_tools


def _bind_tools(node_fn, tools: list[BaseTool]):
    @functools.wraps(node_fn)
    async def wrapper(state: OutingState) -> dict:
        return await node_fn(state, tools)
    return wrapper


def _route_by_type(state: OutingState) -> str:
    outing_type = state["outing_type"]
    if outing_type == "both":
        return "parallel_both"
    elif outing_type == "activity":
        return "activity_search"
    else:
        return "lunch_search"


def _route_after_lunch_search(state: OutingState) -> str:
    return "score_lunch"


def _route_after_activity_search(state: OutingState) -> str:
    return "score_activity"


async def build_graph(tools: list[BaseTool]) -> StateGraph:
    geocode = _bind_tools(geocode_node, tools)
    weather = _bind_tools(weather_node, tools)
    lunch_search = _bind_tools(lunch_search_node, tools)
    activity_search = _bind_tools(activity_search_node, tools)

    graph = StateGraph(OutingState)

    graph.add_node("geocode", geocode)
    graph.add_node("fetch_weather", weather)
    graph.add_node("lunch_search", lunch_search)
    graph.add_node("activity_search", activity_search)
    graph.add_node("score_lunch", score_lunch_node)
    graph.add_node("score_activity", score_activity_node)

    graph.add_node("parallel_lunch_search", lunch_search)
    graph.add_node("parallel_activity_search", activity_search)
    graph.add_node("plan_both", plan_both_node)

    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "fetch_weather")

    graph.add_conditional_edges(
        "fetch_weather",
        _route_by_type,
        {
            "lunch_search": "lunch_search",
            "activity_search": "activity_search",
            "parallel_both": "parallel_lunch_search",
        },
    )

    # Single-mode paths
    graph.add_edge("lunch_search", "score_lunch")
    graph.add_edge("score_lunch", END)

    graph.add_edge("activity_search", "score_activity")
    graph.add_edge("score_activity", END)

    # Both-mode: parallel search then combine
    graph.add_edge("parallel_lunch_search", "parallel_activity_search")
    graph.add_edge("parallel_activity_search", "plan_both")
    graph.add_edge("plan_both", END)

    return graph.compile()


async def run_outing_agent(
    location: str,
    team_size: int,
    budget_per_head: int,
    outing_type: str,
    available_time: str,
    llm_provider: str = "groq",
) -> dict:
    start_time = time.time()
    print(f"[AGENT] Starting: location={location}, type={outing_type}, provider={llm_provider}", flush=True)

    exit_stack = AsyncExitStack()
    try:
        print("[AGENT] Creating MCP tools...", flush=True)
        tools = await create_mcp_tools(exit_stack)
        tool_names = [t.name for t in tools]
        print(f"[AGENT] MCP tools ready: {len(tools)} tools", flush=True)

        compiled_graph = await build_graph(tools)
        print("[AGENT] Graph compiled, invoking...", flush=True)

        initial_state: OutingState = {
            "location": location,
            "team_size": team_size,
            "budget_per_head": budget_per_head,
            "outing_type": outing_type,
            "available_time": available_time,
            "llm_provider": llm_provider,
            "lat": 0.0,
            "lng": 0.0,
            "weather_data": {},
            "places_raw": [],
            "search_results": "",
            "activity_places_raw": [],
            "activity_search_results": "",
            "plans": [],
            "agent_info": {},
            "error": "",
        }

        result = await compiled_graph.ainvoke(initial_state)
        print(f"[AGENT] Graph completed, plans={len(result.get('plans', []))}", flush=True)

        elapsed = round(time.time() - start_time, 1)
        result["agent_info"] = {
            "llm_provider": llm_provider,
            "mcp_servers": list(
                {
                    "tavily-search",
                    "google-maps",
                    "weather",
                }
            ),
            "tools_available": tool_names,
            "elapsed_seconds": elapsed,
        }

        return result

    finally:
        await exit_stack.aclose()
