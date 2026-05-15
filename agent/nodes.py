from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool

from agent.llm import get_llm
from agent.state import OutingState
from agent.prompts import LUNCH_SCORE_PROMPT, ACTIVITY_SCORE_PROMPT, BOTH_PLAN_PROMPT


async def _call_tool(tools: list[BaseTool], name: str, args: dict) -> Any:
    for tool in tools:
        if tool.name == name:
            return await tool.ainvoke(args)
    raise ValueError(f"Tool '{name}' not found. Available: {[t.name for t in tools]}")


async def _find_tool(tools: list[BaseTool], *candidates: str) -> BaseTool | None:
    tool_names = {t.name for t in tools}
    for name in candidates:
        if name in tool_names:
            return name
    return None


def _parse_places_response(raw: Any) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
    elif isinstance(raw, dict):
        parsed = raw
    else:
        return []
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("places", "results", "data"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
    return []


async def geocode_node(state: OutingState, tools: list[BaseTool]) -> dict:
    print(f"[NODE] geocode_node START", flush=True)
    tool_name = await _find_tool(tools, "maps_geocode", "geocode")
    if not tool_name:
        llm = get_llm(state["llm_provider"])
        resp = await llm.ainvoke([HumanMessage(
            content=f"What are the latitude and longitude coordinates of {state['location']}? "
            "Return ONLY a JSON object with keys 'lat' and 'lng', nothing else."
        )])
        coords = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
        return {"lat": coords["lat"], "lng": coords["lng"]}

    result = await _call_tool(tools, tool_name, {"address": state["location"]})
    if isinstance(result, str) and result.strip():
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, ValueError):
            result = {}
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    if isinstance(result, dict):
        loc = result.get("location", result)
        if isinstance(loc, dict):
            lat = loc.get("latitude", loc.get("lat", 0))
            lng = loc.get("longitude", loc.get("lng", 0))
        else:
            lat = result.get("latitude", result.get("lat", 0))
            lng = result.get("longitude", result.get("lng", 0))
    else:
        lat, lng = 0, 0
    print(f"[NODE] geocode_node END lat={lat}, lng={lng}", flush=True)
    return {"lat": lat, "lng": lng}


async def weather_node(state: OutingState, tools: list[BaseTool]) -> dict:
    print(f"[NODE] weather_node START", flush=True)
    lat, lng = state["lat"], state["lng"]

    tool_name = await _find_tool(tools, "get-forecast", "get_current_weather", "get_forecast")
    if tool_name:
        result = await _call_tool(tools, tool_name, {"latitude": lat, "longitude": lng})
        weather_text = result if isinstance(result, str) else json.dumps(result)
    else:
        weather_text = f"Weather data unavailable for {lat}, {lng}"

    is_outdoor = True
    lower = weather_text.lower()
    if any(w in lower for w in ["rain", "storm", "thunder", "heavy"]):
        is_outdoor = False

    temp = 0.0
    for token in weather_text.split():
        try:
            val = float(token.replace("°", "").replace("C", "").replace("F", ""))
            if -50 < val < 60:
                temp = val
                break
        except ValueError:
            continue

    print(f"[NODE] weather_node END outdoor={is_outdoor}, temp={temp}", flush=True)
    return {
        "weather_data": {
            "temperature_c": temp,
            "condition": weather_text[:200],
            "is_outdoor_friendly": is_outdoor,
            "summary": weather_text[:300],
        }
    }


async def lunch_search_node(state: OutingState, tools: list[BaseTool]) -> dict:
    print(f"[NODE] lunch_search_node START", flush=True)
    lat, lng = state["lat"], state["lng"]

    places_result = []
    search_text = ""

    maps_tool = await _find_tool(tools, "maps_search_places", "search_places", "maps_nearby_search")
    if maps_tool:
        raw = await _call_tool(tools, maps_tool, {
            "query": f"restaurants near {state['location']}",
            "location": f"{lat},{lng}",
            "radius": 3000,
        })
        places_result = _parse_places_response(raw)

    search_tool = await _find_tool(tools, "tavily_search", "tavily-search", "search")
    if search_tool:
        raw = await _call_tool(tools, search_tool, {
            "query": f"best team lunch restaurants near {state['location']} for {state['team_size']} people budget {state['budget_per_head']} per head 2026"
        })
        search_text = raw if isinstance(raw, str) else json.dumps(raw)

    print(f"[NODE] lunch_search_node END places={len(places_result)}, search_len={len(search_text)}", flush=True)
    return {
        "places_raw": places_result,
        "search_results": search_text[:3000],
    }


async def activity_search_node(state: OutingState, tools: list[BaseTool]) -> dict:
    print(f"[NODE] activity_search_node START", flush=True)
    lat, lng = state["lat"], state["lng"]

    places_result = []
    search_text = ""

    maps_tool = await _find_tool(tools, "maps_search_places", "search_places", "maps_nearby_search")
    if maps_tool:
        raw = await _call_tool(tools, maps_tool, {
            "query": f"team activities bowling escape room near {state['location']}",
            "location": f"{lat},{lng}",
            "radius": 5000,
        })
        places_result = _parse_places_response(raw)

    search_tool = await _find_tool(tools, "tavily_search", "tavily-search", "search")
    if search_tool:
        raw = await _call_tool(tools, search_tool, {
            "query": f"best team outing activities near {state['location']} for {state['team_size']} people bowling laser tag escape room 2026"
        })
        search_text = raw if isinstance(raw, str) else json.dumps(raw)

    print(f"[NODE] activity_search_node END places={len(places_result)}, search_len={len(search_text)}", flush=True)
    return {
        "activity_places_raw": places_result,
        "activity_search_results": search_text[:3000],
    }


async def score_lunch_node(state: OutingState) -> dict:
    print(f"[NODE] score_lunch_node START provider={state['llm_provider']}", flush=True)
    llm = get_llm(state["llm_provider"])

    prompt = LUNCH_SCORE_PROMPT.format(
        location=state["location"],
        team_size=state["team_size"],
        budget_per_head=state["budget_per_head"],
        available_time=state["available_time"],
        weather=json.dumps(state["weather_data"], indent=2),
        places=json.dumps(state.get("places_raw", []), indent=2)[:4000],
        search_results=state.get("search_results", "No search results available"),
    )

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        restaurants = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                restaurants = json.loads(text[start:end])
            except (json.JSONDecodeError, ValueError):
                restaurants = []
        else:
            restaurants = []

    plans = []
    for i, r in enumerate(restaurants[:3]):
        plans.append({
            "rank": i + 1,
            "label": ["Best Overall", "Great Value", "Hidden Gem"][i],
            "restaurant": r,
            "activity": None,
            "total_cost_per_head": r.get("estimated_cost_per_head", 0),
            "total_time_min": r.get("travel_time_min", 0) + 60,
            "time_breakdown": {
                "travel_to_lunch": r.get("travel_time_min", 0),
                "lunch_duration": 60,
            },
            "why_chosen": r.get("why_chosen", ""),
        })

    print(f"[NODE] score_lunch_node END plans={len(plans)}", flush=True)
    return {"plans": plans}


async def score_activity_node(state: OutingState) -> dict:
    print(f"[NODE] score_activity_node START provider={state['llm_provider']}", flush=True)
    llm = get_llm(state["llm_provider"])

    prompt = ACTIVITY_SCORE_PROMPT.format(
        location=state["location"],
        team_size=state["team_size"],
        budget_per_head=state["budget_per_head"],
        available_time=state["available_time"],
        weather=json.dumps(state["weather_data"], indent=2),
        places=json.dumps(state.get("activity_places_raw", state.get("places_raw", [])), indent=2)[:4000],
        search_results=state.get("activity_search_results", state.get("search_results", "No search results")),
    )

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        activities = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                activities = json.loads(text[start:end])
            except (json.JSONDecodeError, ValueError):
                activities = []
        else:
            activities = []

    plans = []
    for i, a in enumerate(activities[:3]):
        duration = a.get("estimated_duration_min", 60)
        plans.append({
            "rank": i + 1,
            "label": ["Best Overall", "Most Fun", "Budget Friendly"][i],
            "activity": a,
            "restaurant": None,
            "total_cost_per_head": a.get("estimated_cost_per_head", 0),
            "total_time_min": a.get("travel_time_min", 0) + duration,
            "time_breakdown": {
                "travel_to_activity": a.get("travel_time_min", 0),
                "activity_duration": duration,
            },
            "why_chosen": a.get("why_chosen", ""),
        })

    print(f"[NODE] score_activity_node END plans={len(plans)}", flush=True)
    return {"plans": plans}


async def plan_both_node(state: OutingState) -> dict:
    print(f"[NODE] plan_both_node START places={len(state.get('places_raw',[]))}, activities={len(state.get('activity_places_raw',[]))}", flush=True)
    llm = get_llm(state["llm_provider"])

    prompt = BOTH_PLAN_PROMPT.format(
        location=state["location"],
        team_size=state["team_size"],
        budget_per_head=state["budget_per_head"],
        available_time=state["available_time"],
        weather=json.dumps(state["weather_data"], indent=2),
        activities=json.dumps(state.get("activity_places_raw", []), indent=2)[:3000],
        restaurants=json.dumps(state.get("places_raw", []), indent=2)[:3000],
    )

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        plans = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                plans = json.loads(text[start:end])
            except (json.JSONDecodeError, ValueError):
                plans = []
        else:
            plans = []

    print(f"[NODE] plan_both_node END plans={len(plans[:3])}", flush=True)
    return {"plans": plans[:3]}
