import React, { useState } from "react";
import type { OutingRequest } from "../api";

interface Props {
  onSubmit: (req: OutingRequest) => void;
  loading: boolean;
}

export default function InputForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<OutingRequest>({
    location: "",
    team_size: 10,
    budget_per_head: 500,
    outing_type: "lunch",
    available_time: "1 hour",
    llm_provider: "groq",
    claude_password: "",
  });

  const set = (key: keyof OutingRequest, value: string | number) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.location.trim()) return;
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h1 style={styles.title}>OutingAI</h1>
      <p style={styles.subtitle}>Plan your team outing in seconds</p>

      <label style={styles.label}>
        Office Location
        <input
          style={styles.input}
          type="text"
          placeholder="e.g. Hitech City, Hyderabad"
          value={form.location}
          onChange={(e) => set("location", e.target.value)}
          required
        />
      </label>

      <div style={styles.row}>
        <label style={{ ...styles.label, flex: 1 }}>
          Team Size
          <input
            style={styles.input}
            type="number"
            min={2}
            max={100}
            value={form.team_size}
            onChange={(e) => set("team_size", +e.target.value)}
          />
        </label>
        <label style={{ ...styles.label, flex: 1 }}>
          Budget/head (INR)
          <input
            style={styles.input}
            type="number"
            min={100}
            step={50}
            value={form.budget_per_head}
            onChange={(e) => set("budget_per_head", +e.target.value)}
          />
        </label>
      </div>

      <label style={styles.label}>
        Outing Type
        <div style={styles.radioGroup}>
          {(["lunch", "activity", "both"] as const).map((t) => (
            <label key={t} style={styles.radioLabel}>
              <input
                type="radio"
                name="outing_type"
                value={t}
                checked={form.outing_type === t}
                onChange={() => set("outing_type", t)}
              />
              {t === "both" ? "Lunch + Activity" : t.charAt(0).toUpperCase() + t.slice(1)}
            </label>
          ))}
        </div>
      </label>

      <label style={styles.label}>
        Available Time
        <select
          style={styles.input}
          value={form.available_time}
          onChange={(e) => set("available_time", e.target.value)}
        >
          <option value="1 hour">1 hour</option>
          <option value="2 hours">2 hours</option>
          <option value="half day">Half day</option>
        </select>
      </label>

      <label style={styles.label}>
        AI Provider
        <select
          style={styles.input}
          value={form.llm_provider}
          onChange={(e) => set("llm_provider", e.target.value)}
        >
          <option value="groq">Groq - Llama 3.3 (Free)</option>
          <option value="gemini">Gemini Flash (Free)</option>
          <option value="claude">Claude Sonnet (Paid - Password Required)</option>
        </select>
      </label>

      {form.llm_provider === "claude" && (
        <label style={styles.label}>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            Claude Access Password
            <span style={{ fontSize: 11, fontWeight: 400, color: "#e53935" }}>Required</span>
          </span>
          <input
            style={{ ...styles.input, borderColor: "#e53935" }}
            type="password"
            placeholder="Enter password for Claude access"
            value={form.claude_password}
            onChange={(e) => set("claude_password", e.target.value)}
            required
          />
        </label>
      )}

      <button type="submit" style={styles.button} disabled={loading}>
        {loading ? "Finding best spots..." : "Find Best Spots"}
      </button>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    maxWidth: 480,
    margin: "0 auto",
    padding: 32,
    background: "#fff",
    borderRadius: 16,
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  },
  title: {
    margin: 0,
    fontSize: 28,
    fontWeight: 700,
    textAlign: "center",
    color: "#1a1a2e",
  },
  subtitle: {
    margin: "4px 0 24px",
    textAlign: "center",
    color: "#666",
    fontSize: 14,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    marginBottom: 16,
    fontSize: 14,
    fontWeight: 600,
    color: "#333",
  },
  input: {
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #ddd",
    fontSize: 15,
    fontWeight: 400,
    outline: "none",
    transition: "border 0.2s",
  },
  row: {
    display: "flex",
    gap: 12,
  },
  radioGroup: {
    display: "flex",
    gap: 16,
    marginTop: 4,
  },
  radioLabel: {
    display: "flex",
    alignItems: "center",
    gap: 4,
    fontWeight: 400,
    cursor: "pointer",
  },
  button: {
    width: "100%",
    padding: "12px 0",
    marginTop: 8,
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
    transition: "opacity 0.2s",
  },
};
