from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class OutingType(str, Enum):
    LUNCH = "lunch"
    ACTIVITY = "activity"
    BOTH = "both"


class AvailableTime(str, Enum):
    ONE_HOUR = "1 hour"
    TWO_HOURS = "2 hours"
    HALF_DAY = "half day"


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    GROQ = "groq"
    GEMINI = "gemini"


class OutingRequest(BaseModel):
    location: str = Field(..., description="Office location e.g. 'Hitech City, Hyderabad'")
    team_size: int = Field(..., ge=2, le=100, description="Number of people")
    budget_per_head: int = Field(..., ge=100, description="Budget per person in INR")
    outing_type: OutingType = Field(..., description="Type of outing")
    available_time: AvailableTime = Field(..., description="Time available")
    llm_provider: LLMProvider = Field(default=LLMProvider.GROQ, description="LLM provider to use")
    claude_password: str = Field(default="", description="Password required for Claude access")


class TimeBreakdown(BaseModel):
    travel: int = Field(description="Travel time in minutes")
    duration: int = Field(description="Activity/lunch duration in minutes")


class Venue(BaseModel):
    name: str
    type: str = ""
    rating: float = 0.0
    review_count: int = 0
    distance_km: float = 0.0
    travel_time_min: int = 0
    travel_mode: str = "driving"
    estimated_cost_per_head: int = 0
    cuisine: str = ""
    group_fit: str = ""
    why_chosen: str = ""
    address: str = ""
    lat: float = 0.0
    lng: float = 0.0
    maps_url: str = ""


class Plan(BaseModel):
    rank: int
    label: str = ""
    activity: Venue | None = None
    restaurant: Venue | None = None
    total_cost_per_head: int = 0
    total_time_min: int = 0
    time_breakdown: dict = {}
    why_chosen: str = ""


class WeatherInfo(BaseModel):
    temperature_c: float = 0.0
    condition: str = ""
    is_outdoor_friendly: bool = True
    summary: str = ""


class OutingResponse(BaseModel):
    weather: WeatherInfo
    plans: list[Plan]
    agent_info: dict = {}
