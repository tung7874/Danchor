const BASE = (import.meta.env.VITE_API_URL ?? "") + "/api/v1";

export async function fetchAnalysis(params: {
  asset_code: string;
  analysis_date?: string;
  holding_horizon_days: number;
}) {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchScan(params: {
  asset_code: string;
  holding_horizon_days: number;
}) {
  const res = await fetch(`${BASE}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPosition(params: {
  asset_code: string;
  entry_date: string;
  entry_price: number;
  current_date?: string;
  current_price: number;
  position_type?: string;
}) {
  const res = await fetch(`${BASE}/position`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
  }
  return res.json();
}
