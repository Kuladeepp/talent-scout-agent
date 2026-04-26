import type { ScoutResponse, JDStruct, Conversation, Weights } from "./types";

const BACKEND = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function scout(input: { jd_text?: string; jd_url?: string; weights: Weights }): Promise<ScoutResponse> {
  const r = await fetch(`${BACKEND}/scout`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`scout failed: ${r.status} ${await r.text()}`);
  return r.json();
}

export async function explain(input: {
  jd: JDStruct;
  candidate_id: string;
  conversation: Conversation;
  interest_score: number;
}): Promise<{ explanation: string }> {
  const r = await fetch(`${BACKEND}/explain`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`explain failed: ${r.status}`);
  return r.json();
}
