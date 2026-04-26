"use client";

import { useEffect, useMemo, useState } from "react";
import { JdInput } from "@/components/JdInput";
import { WeightSliders } from "@/components/WeightSliders";
import { ResultsTable } from "@/components/ResultsTable";
import { CandidateDetailPanel } from "@/components/CandidateDetailPanel";
import { toast } from "sonner";
import type { ScoutResponse, Weights, RankedRow } from "@/lib/types";

const LOADING_STAGES = [
  "Parsing job description...",
  "Embedding JD and retrieving top 20 candidates...",
  "Scoring 20 candidates in parallel (Gemini 2.5)...",
  "Simulating outreach conversations for top 10...",
  "Scoring candidate interest from transcripts...",
  "Combining match + interest into final ranking...",
  "Almost there — Vertex AI is finishing up...",
  "Cold start in progress, hang on (first run can take a few minutes)...",
  "Still processing — large pipelines sometimes take longer...",
  "Backend is working, response is on the way...",
];

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
  const [stageIdx, setStageIdx] = useState(0);

  useEffect(() => {
    if (!loading) return;
    setStageIdx(0);
    const timer = setInterval(() => {
      setStageIdx((i) => Math.min(i + 1, LOADING_STAGES.length - 1));
    }, 18_000); // advance message every ~18s
    return () => clearInterval(timer);
  }, [loading]);

  const ranked = useMemo(() => (resp ? rerank(resp, weights) : []), [resp, weights]);

  const handleScout = async (input: { jd_text?: string; jd_url?: string }) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!backendUrl) {
      toast.error("Frontend missing NEXT_PUBLIC_BACKEND_URL — check Vercel env vars");
      return;
    }
    setLoading(true);
    setOpenCid(null);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 600_000); // 10 min timeout — matches Cloud Run max
      const r = await fetch(`${backendUrl}/scout`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...input, weights }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
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
      if (e instanceof DOMException && e.name === "AbortError") {
        toast.error("Request timed out (10 min). The backend may still be processing — try the same JD again, it will be cached.");
      } else {
        toast.error((e instanceof Error ? e.message : null) ?? "Scout failed");
      }
    } finally {
      setLoading(false);
    }
  };

  const openRow = ranked.find((r) => r.candidate_id === openCid) ?? null;
  const match = openCid && resp ? resp.match_details[openCid] ?? null : null;
  const interest = openCid && resp ? resp.interest_details[openCid] ?? null : null;

  const detailOpen = openCid !== null;

  return (
    <div className="bg-gradient-to-b from-slate-50 to-slate-100 min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white shrink-0">
        <div className="mx-auto max-w-screen-2xl px-6 py-4 flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm">TS</div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-slate-900">Talent Scout Agent</h1>
            <p className="text-xs text-slate-500">JD → matched candidates → simulated outreach → ranked shortlist</p>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        {/* Input section */}
        <div className="mx-auto w-full max-w-screen-2xl px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
            <div className="lg:col-span-3">
              <JdInput onSubmit={handleScout} loading={loading} loadingMessage={LOADING_STAGES[stageIdx]} />
            </div>
            <div>
              <WeightSliders weights={weights} onChange={setWeights} />
            </div>
          </div>
        </div>

        {/* Results section — split panel */}
        {resp && (
          <div className="flex-1 flex flex-col border-t border-slate-200 bg-white">
            {/* Results toolbar */}
            <div className="mx-auto w-full max-w-screen-2xl px-6 py-3 flex items-center justify-between border-b border-slate-100">
              <div className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{resp.jd.role}</span>
                <span className="mx-2 text-slate-300">·</span>
                <span>{resp.jd.skills_required.slice(0, 4).join(", ")}</span>
                <span className="mx-2 text-slate-300">·</span>
                <span className="text-slate-500">{ranked.length} candidates</span>
              </div>
            </div>

            {/* Split layout */}
            <div className="flex-1 flex overflow-hidden">
              {/* Table panel */}
              <div className={`transition-all duration-200 ease-in-out overflow-y-auto ${
                detailOpen ? "w-1/2 xl:w-3/5" : "w-full"
              }`}>
                <div className={detailOpen ? "p-4" : "mx-auto max-w-screen-2xl px-6 py-4"}>
                  <ResultsTable
                    rows={ranked}
                    onRowClick={setOpenCid}
                    selectedCid={openCid}
                    compact={detailOpen}
                  />
                </div>
              </div>

              {/* Detail panel */}
              {detailOpen && (
                <div className="w-1/2 xl:w-2/5 shrink-0 overflow-hidden border-l border-slate-200 animate-in slide-in-from-right-4 duration-200">
                  <CandidateDetailPanel
                    jd={resp.jd}
                    candidateId={openCid}
                    candidateName={openRow?.name ?? ""}
                    candidateTitle={openRow?.title}
                    match={match}
                    interest={interest}
                    onClose={() => setOpenCid(null)}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
