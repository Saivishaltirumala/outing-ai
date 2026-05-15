from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict
from langgraph.graph import MessagesState


class OutingState(TypedDict):
    # --- inputs ---
    location: str
    team_size: int
    budget_per_head: int
    outing_type: str
    available_time: str
    llm_provider: str

    # --- intermediate ---
    lat: float
    lng: float
    weather_data: dict
    places_raw: list[dict]
    search_results: str
    activity_places_raw: list[dict]
    activity_search_results: str

    # --- output ---
    plans: list[dict]
    agent_info: dict
    error: str
