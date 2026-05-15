export interface OutingRequest {
  location: string;
  team_size: number;
  budget_per_head: number;
  outing_type: "lunch" | "activity" | "both";
  available_time: "1 hour" | "2 hours" | "half day";
  llm_provider: "claude" | "groq" | "gemini";
  claude_password: string;
}

export interface Venue {
  name: string;
  type: string;
  rating: number;
  review_count: number;
  distance_km: number;
  travel_time_min: number;
  travel_mode: string;
  estimated_cost_per_head: number;
  cuisine: string;
  group_fit: string;
  why_chosen: string;
  address: string;
  lat: number;
  lng: number;
  maps_url: string;
}

export interface Plan {
  rank: number;
  label: string;
  activity: Venue | null;
  restaurant: Venue | null;
  total_cost_per_head: number;
  total_time_min: number;
  time_breakdown: Record<string, number>;
  why_chosen: string;
}

export interface WeatherInfo {
  temperature_c: number;
  condition: string;
  is_outdoor_friendly: boolean;
  summary: string;
}

export interface OutingResponse {
  weather: WeatherInfo;
  plans: Plan[];
  agent_info: Record<string, unknown>;
}

const API_BASE = window.location.origin;

export async function planOuting(req: OutingRequest): Promise<OutingResponse> {
  const res = await fetch(`${API_BASE}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}
