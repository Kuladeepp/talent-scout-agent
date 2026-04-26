"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X, Sparkles, CheckCircle2, AlertCircle, MessageSquare } from "lucide-react";
import type { JDStruct, MatchResult, InterestResult } from "@/lib/types";

type Props = {
  jd: JDStruct | null;
  candidateId: string | null;
  candidateName: string;
  candidateTitle?: string;
  match: MatchResult | null;
  interest: InterestResult | null;
  onClose: () => void;
};

export function CandidateDetailPanel(p: Props) {
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);

  const askExplain = async () => {
    if (!p.jd || !p.candidateId || !p.interest) return;
    setExplaining(true);
    setExplanation(null);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const r = await fetch(`${backendUrl}/explain`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          jd: p.jd,
          candidate_id: p.candidateId,
          conversation: p.interest.conversation,
          interest_score: p.interest.interest_score,
        }),
      });
      const data = await r.json();
      setExplanation(data.explanation || data.error || "no explanation");
    } finally {
      setExplaining(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-l border-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-slate-900 truncate">{p.candidateName}</h2>
          {p.candidateTitle && (
            <p className="text-xs text-slate-500 truncate mt-0.5">{p.candidateTitle}</p>
          )}
        </div>
        <button
          onClick={p.onClose}
          className="ml-3 shrink-0 p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Score summary bar */}
      {p.match && (
        <div className="flex items-center gap-3 px-5 py-3 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500 uppercase tracking-wide font-medium">Match</span>
            <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${
              p.match.match_score >= 80 ? "bg-emerald-100 text-emerald-700" :
              p.match.match_score >= 60 ? "bg-amber-100 text-amber-700" :
              "bg-slate-100 text-slate-600"
            }`}>{p.match.match_score}</span>
          </div>
          {p.interest && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500 uppercase tracking-wide font-medium">Interest</span>
              <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${
                p.interest.interest_score >= 80 ? "bg-emerald-100 text-emerald-700" :
                p.interest.interest_score >= 60 ? "bg-amber-100 text-amber-700" :
                "bg-slate-100 text-slate-600"
              }`}>{p.interest.interest_score}</span>
            </div>
          )}
        </div>
      )}

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto">
        {/* Match reasoning */}
        {p.match && (
          <div className="px-5 py-4 border-b border-slate-100">
            <div className="flex items-center gap-2 mb-2.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Match Analysis</h3>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">{p.match.reasoning}</p>

            {p.match.matched_skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {p.match.matched_skills.map((s) => (
                  <span key={s} className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
                    <CheckCircle2 className="w-3 h-3" />{s}
                  </span>
                ))}
              </div>
            )}
            {p.match.missing_skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {p.match.missing_skills.map((s) => (
                  <span key={s} className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-medium text-red-600 ring-1 ring-inset ring-red-200">
                    <AlertCircle className="w-3 h-3" />{s}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Conversation */}
        {p.interest && p.interest.conversation.turns.length > 0 && (
          <div className="px-5 py-4">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-3.5 h-3.5 text-indigo-500" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Simulated Outreach</h3>
            </div>

            <div className="space-y-3">
              {p.interest.conversation.turns.map((t, idx) => (
                <div
                  key={idx}
                  className={`flex ${t.speaker === "recruiter" ? "justify-start" : "justify-end"}`}
                >
                  <div className={`max-w-[88%] ${
                    t.speaker === "recruiter"
                      ? "rounded-2xl rounded-bl-md bg-indigo-600 text-white"
                      : "rounded-2xl rounded-br-md bg-slate-100 text-slate-800"
                  }`}>
                    <div className={`px-3.5 pt-2 pb-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      t.speaker === "recruiter" ? "text-indigo-200" : "text-slate-400"
                    }`}>
                      {t.speaker}
                    </div>
                    <div className="px-3.5 pb-3 text-[13px] leading-relaxed">
                      {t.text}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {p.interest.signals.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {p.interest.signals.map((s, i) => (
                  <Badge key={i} variant="outline" className="text-[11px] font-normal">{s}</Badge>
                ))}
              </div>
            )}

            {p.interest.summary && (
              <p className="mt-3 text-xs text-slate-500 italic">{p.interest.summary}</p>
            )}

            <div className="mt-4 pt-3 border-t border-slate-100">
              <Button onClick={askExplain} disabled={explaining} variant="outline" size="sm" className="text-xs">
                <Sparkles className="w-3 h-3 mr-1.5" />
                {explaining ? "Analyzing..." : "Explain this conversation"}
              </Button>
              {explanation && (
                <div className="mt-3 p-3 rounded-lg bg-violet-50 border border-violet-100">
                  <p className="text-xs text-violet-800 leading-relaxed whitespace-pre-wrap">{explanation}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* No outreach data */}
        {(!p.interest || p.interest.conversation.turns.length === 0) && p.match && (
          <div className="px-5 py-8 text-center text-sm text-slate-400">
            No outreach conversation for this candidate.
          </div>
        )}
      </div>
    </div>
  );
}
