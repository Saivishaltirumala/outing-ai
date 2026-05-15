import React, { useState } from "react";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import { planOuting, type OutingRequest, type OutingResponse } from "./api";

export default function App() {
  const [result, setResult] = useState<OutingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (req: OutingRequest) => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await planOuting(req);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.app}>
      {!result ? (
        <>
          <InputForm onSubmit={handleSubmit} loading={loading} />
          {loading && (
            <div style={styles.loadingBar}>
              <div style={styles.spinner} />
              <span>Querying 3 MCP servers and scoring venues...</span>
            </div>
          )}
          {error && <div style={styles.error}>{error}</div>}
        </>
      ) : (
        <Results data={result} onReset={() => setResult(null)} />
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
    padding: "40px 16px",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  loadingBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    marginTop: 20,
    fontSize: 14,
    color: "#555",
  },
  spinner: {
    width: 18,
    height: 18,
    border: "3px solid #ddd",
    borderTop: "3px solid #667eea",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  error: {
    maxWidth: 480,
    margin: "16px auto",
    padding: "12px 16px",
    background: "#ffeaea",
    color: "#c62828",
    borderRadius: 10,
    fontSize: 14,
    textAlign: "center",
  },
};
