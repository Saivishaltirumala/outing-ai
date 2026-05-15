from __future__ import annotations

import os
import json
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import OutingRequest, OutingResponse, WeatherInfo, Plan, Venue
from agent.graph import run_outing_agent

router = APIRouter()


def _validate_claude_access(password: str) -> bool:
    correct_password = os.getenv("CLAUDE_ACCESS_PASSWORD", "")
    if not correct_password:
        return False
    return password == correct_password


def _parse_venue(data: dict | None) -> Venue | None:
    if not data:
        return None
    try:
        return Venue(
            name=str(data.get("name", "Unknown")),
            type=str(data.get("type", data.get("cuisine", ""))),
            rating=float(data.get("rating", 0) or 0),
            review_count=int(data.get("review_count", 0) or 0),
            distance_km=float(data.get("distance_km", 0) or 0),
            travel_time_min=int(data.get("travel_time_min", 0) or 0),
            travel_mode=str(data.get("travel_mode", "driving")),
            estimated_cost_per_head=int(data.get("estimated_cost_per_head", 0) or 0),
            cuisine=str(data.get("cuisine", "")),
            group_fit=str(data.get("group_fit", "")),
            why_chosen=str(data.get("why_chosen", "")),
            address=str(data.get("address", "")),
            lat=float(data.get("lat", 0) or 0),
            lng=float(data.get("lng", 0) or 0),
            maps_url=str(data.get("maps_url", "")),
        )
    except Exception:
        return Venue(name=str(data.get("name", "Unknown")))


@router.post("/api/plan", response_model=OutingResponse)
async def plan_outing(request: OutingRequest):
    if request.llm_provider.value == "claude":
        if not _validate_claude_access(request.claude_password):
            raise HTTPException(
                status_code=403,
                detail="Invalid password. Claude requires authorized access."
            )

    print(f"[ROUTE] /api/plan called: location={request.location}, type={request.outing_type.value}, provider={request.llm_provider.value}", flush=True)
    try:
        result = await run_outing_agent(
            location=request.location,
            team_size=request.team_size,
            budget_per_head=request.budget_per_head,
            outing_type=request.outing_type.value,
            available_time=request.available_time.value,
            llm_provider=request.llm_provider.value,
        )

        weather_data = result.get("weather_data", {})
        weather = WeatherInfo(
            temperature_c=weather_data.get("temperature_c", 0),
            condition=weather_data.get("condition", ""),
            is_outdoor_friendly=weather_data.get("is_outdoor_friendly", True),
            summary=weather_data.get("summary", ""),
        )

        plans = []
        for p in result.get("plans", []):
            plans.append(Plan(
                rank=p.get("rank", 0),
                label=p.get("label", ""),
                activity=_parse_venue(p.get("activity")),
                restaurant=_parse_venue(p.get("restaurant")),
                total_cost_per_head=int(p.get("total_cost_per_head", 0)),
                total_time_min=int(p.get("total_time_min", 0)),
                time_breakdown=p.get("time_breakdown", {}),
                why_chosen=p.get("why_chosen", ""),
            ))

        print(f"[ROUTE] Success: {len(plans)} plans", flush=True)
        return OutingResponse(
            weather=weather,
            plans=plans,
            agent_info=result.get("agent_info", {}),
        )

    except Exception as e:
        print(f"[ROUTE] ERROR: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
