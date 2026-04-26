"use client";

import { useMemo, useState } from "react";
import { JdInput } from "@/components/JdInput";
import { WeightSliders } from "@/components/WeightSliders";
import { ResultsTable } from "@/components/ResultsTable";
import { ConversationDrawer } from "@/components/ConversationDrawer";
import { toast } from "sonner";
import type { ScoutResponse, Weights, RankedRow } from "@/lib/types";

function rerank(resp: ScoutResponse, w: Weights): RankedRow[] {
  return [...resp.ranked]
    .map((r) => {
      if (r.interest_score === null) return { ...r, final_score: r.match_score };
      const f = w.match * r.match_score + w.interest * r.interest_score;
      return { ...r, final_score: Math.round(f * 100) / 100 };
    })
    .sort((a, b) => b.final_score - a.final_score);
}

export default function Home() {
  const [resp, setResp] = useState<ScoutResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [weights, setWeights] = useState<Weights>({ match: 0.6, interest: 0.4 });
  const [openCid, setOpenCid] = useState<string | null>(null);

  const ranked = useMemo(() => (resp ? rerank(resp, weights) : []), [resp, weights]);

  const handleScout = async (input: { jd_text?: string; jd_url?: string }) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!backendUrl) {
      toast.error("Frontend missing NEXT_PUBLIC_BACKEND_URL — check Vercel env vars");
      return;
    }
    setLoading(true);
    try {
      // Call backend directly (Vercel free plan has 10s timeout on route handlers,
      // but the pipeline can take 60-120s on first call. CORS is open on the backend.)
      const r = await fetch(`${backendUrl}/scout`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...input, weights }),
      });
      if (!r.ok) {
        throw new Error(`Backend returned ${r.status} ${r.statusText}`);
      }
      const contentType = r.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Backend did not return JSON");
      }
      const data: ScoutResponse = await r.json();
      setResp(data);
      toast.success(`Found ${data.ranked.length} candidates`);
    } catch (e: unknown) {
      toast.error((e instanceof Error ? e.message : null) ?? "Scout failed");
    } finally {
      setLoading(false);
    }
  };

  const openRow = ranked.find((r) => r.candidate_id === openCid) ?? null;
  const match = openCid && resp ? resp.match_details[openCid] ?? null : null;
  const interest = openCid && resp ? resp.interest_details[openCid] ?? null : null;

  return (
    <div className="bg-gradient-to-b from-slate-50 to-slate-100 min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5 flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold">TS</div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Talent Scout Agent</h1>
            <p className="text-xs text-slate-500">JD → matched candidates → simulated outreach → ranked shortlist</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 space-y-6">

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <JdInput onSubmit={handleScout} loading={loading} />
        </div>
        <div>
          <WeightSliders weights={weights} onChange={setWeights} />
        </div>
      </div>

      {resp && (
        <section className="space-y-3">
          <div className="text-sm text-slate-600">
            Parsed role: <span className="font-medium">{resp.jd.role}</span> ·{" "}
            {resp.jd.skills_required.slice(0, 5).join(", ")}
          </div>
          <ResultsTable rows={ranked} onRowClick={setOpenCid} />
        </section>
      )}

      <ConversationDrawer
        open={openCid !== null}
        onOpenChange={(o) => !o && setOpenCid(null)}
        jd={resp?.jd ?? null}
        candidateId={openCid}
        candidateName={openRow?.name ?? ""}
        match={match}
        interest={interest}
      />
      </main>
    </div>
  );
}
