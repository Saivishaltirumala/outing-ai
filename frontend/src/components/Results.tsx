import React from "react";
import type { OutingResponse, Plan, Venue } from "../api";

interface Props {
  data: OutingResponse;
  onReset: () => void;
}

const RANK_ICONS = ["", "\u{1F947}", "\u{1F948}", "\u{1F949}"];

function VenueCard({ venue, heading }: { venue: Venue; heading: string }) {
  return (
    <div style={styles.venueCard}>
      <div style={styles.venueHeading}>{heading}</div>
      <div style={styles.venueName}>{venue.name}</div>
      <div style={styles.venueDetails}>
        <span>{"⭐"} {venue.rating} ({venue.review_count} reviews)</span>
        <span>{"\u{1F4CD}"} {venue.distance_km} km &middot; {venue.travel_time_min} min {venue.travel_mode}</span>
      </div>
      <div style={styles.venueDetails}>
        <span>{"\u{1F4B0}"} ~{"₹"}{venue.estimated_cost_per_head}/head</span>
        {venue.cuisine && <span>{"\u{1F37D}️"} {venue.cuisine}</span>}
        {venue.type && !venue.cuisine && <span>{"\u{1F3AF}"} {venue.type}</span>}
      </div>
      {venue.group_fit && venue.group_fit !== "True" && venue.group_fit !== "true" && venue.group_fit !== "False" && venue.group_fit !== "false" && (
        <div style={styles.groupFit}>{"\u{1F465}"} {venue.group_fit}</div>
      )}
      {venue.why_chosen && (
        <div style={styles.whyChosen}>{"✅"} {venue.why_chosen}</div>
      )}
      {venue.maps_url && (
        <a href={venue.maps_url} target="_blank" rel="noreferrer" style={styles.mapsLink}>
          {"\u{1F4CD}"} View on Maps
        </a>
      )}
    </div>
  );
}

function PlanCard({ plan }: { plan: Plan }) {
  const icon = RANK_ICONS[plan.rank] || "";
  return (
    <div style={styles.planCard}>
      <div style={styles.planHeader}>
        <span style={styles.planRank}>{icon} #{plan.rank}</span>
        <span style={styles.planLabel}>{plan.label}</span>
      </div>

      {plan.activity && <VenueCard venue={plan.activity} heading={"\u{1F3AF} Activity"} />}

      {plan.activity && plan.restaurant && (
        <div style={styles.arrow}>{"⬇️"} Travel to lunch</div>
      )}

      {plan.restaurant && <VenueCard venue={plan.restaurant} heading={"\u{1F37D}️ Lunch"} />}

      <div style={styles.planFooter}>
        <span>{"\u{1F4B0}"} Total: {"₹"}{plan.total_cost_per_head}/head</span>
        <span>{"⏱"} {plan.total_time_min} min</span>
      </div>

      {plan.why_chosen && !plan.activity && !plan.restaurant?.why_chosen && (
        <div style={styles.planWhy}>{plan.why_chosen}</div>
      )}
    </div>
  );
}

export default function Results({ data, onReset }: Props) {
  const { weather, plans, agent_info } = data;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.heading}>OutingAI Results</h2>
        <button onClick={onReset} style={styles.resetBtn}>{"←"} New Search</button>
      </div>

      <div style={styles.weatherBar}>
        {weather.is_outdoor_friendly ? "\u{1F324}️" : "\u{1F327}️"}{" "}
        Weather: {weather.temperature_c > 0 ? `${weather.temperature_c}°C` : ""}{" "}
        {weather.is_outdoor_friendly ? "Good for outdoor!" : "Consider indoor options"}
      </div>

      {plans.map((plan) => (
        <PlanCard key={plan.rank} plan={plan} />
      ))}

      <div style={styles.agentBar}>
        {"\u{1F916}"} Agent: {String(agent_info.llm_provider || "").toUpperCase()} |{" "}
        {Array.isArray(agent_info.mcp_servers) ? (agent_info.mcp_servers as string[]).length : 3} MCP servers |{" "}
        Took {String(agent_info.elapsed_seconds ?? "")}s
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 600,
    margin: "0 auto",
    padding: "16px 16px 32px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  heading: {
    margin: 0,
    fontSize: 22,
    fontWeight: 700,
    color: "#1a1a2e",
  },
  resetBtn: {
    padding: "8px 16px",
    background: "#f0f0f0",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 600,
  },
  weatherBar: {
    padding: "12px 16px",
    background: "linear-gradient(135deg, #e0f7fa, #b2ebf2)",
    borderRadius: 12,
    fontSize: 15,
    fontWeight: 600,
    marginBottom: 20,
    textAlign: "center",
  },
  planCard: {
    background: "#fff",
    borderRadius: 14,
    boxShadow: "0 2px 16px rgba(0,0,0,0.07)",
    marginBottom: 20,
    overflow: "hidden",
  },
  planHeader: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "14px 18px",
    background: "linear-gradient(135deg, #667eea, #764ba2)",
    color: "#fff",
  },
  planRank: { fontSize: 18, fontWeight: 700 },
  planLabel: { fontSize: 14, fontWeight: 500, opacity: 0.9 },
  venueCard: {
    padding: "14px 18px",
    borderBottom: "1px solid #f0f0f0",
  },
  venueHeading: {
    fontSize: 12,
    fontWeight: 700,
    textTransform: "uppercase" as const,
    color: "#888",
    marginBottom: 4,
  },
  venueName: { fontSize: 17, fontWeight: 700, color: "#1a1a2e", marginBottom: 8 },
  venueDetails: {
    display: "flex",
    gap: 16,
    fontSize: 13,
    color: "#555",
    marginBottom: 4,
    flexWrap: "wrap" as const,
  },
  groupFit: { fontSize: 13, color: "#555", marginTop: 4 },
  whyChosen: {
    fontSize: 13,
    color: "#2e7d32",
    marginTop: 8,
    lineHeight: 1.5,
  },
  mapsLink: {
    display: "inline-block",
    marginTop: 8,
    fontSize: 13,
    color: "#667eea",
    textDecoration: "none",
    fontWeight: 600,
  },
  arrow: {
    textAlign: "center",
    padding: "6px 0",
    fontSize: 13,
    color: "#999",
  },
  planFooter: {
    display: "flex",
    justifyContent: "space-around",
    padding: "10px 18px",
    fontSize: 14,
    fontWeight: 600,
    color: "#444",
    background: "#fafafa",
  },
  planWhy: {
    padding: "10px 18px 14px",
    fontSize: 13,
    color: "#666",
    lineHeight: 1.5,
  },
  agentBar: {
    padding: "10px 16px",
    background: "#f5f5f5",
    borderRadius: 10,
    fontSize: 13,
    color: "#888",
    textAlign: "center",
  },
};
