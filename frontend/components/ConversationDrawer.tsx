"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import type { JDStruct, MatchResult, InterestResult } from "@/lib/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jd: JDStruct | null;
  candidateId: string | null;
  candidateName: string;
  match: MatchResult | null;
  interest: InterestResult | null;
};

export function ConversationDrawer(p: Props) {
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
    <Sheet open={p.open} onOpenChange={p.onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{p.candidateName}</SheetTitle>
          <SheetDescription>
            Match: {p.match?.match_score ?? "—"} · Interest: {p.interest?.interest_score ?? "—"}
          </SheetDescription>
        </SheetHeader>

        {p.match && (
          <section className="mt-6">
            <h3 className="text-sm font-semibold mb-2">Match reasoning</h3>
            <p className="text-sm text-slate-700">{p.match.reasoning}</p>
            {p.match.matched_skills.length > 0 && (
              <p className="text-xs text-slate-500 mt-2">
                <strong>Matched:</strong> {p.match.matched_skills.join(", ")}
              </p>
            )}
            {p.match.missing_skills.length > 0 && (
              <p className="text-xs text-slate-500">
                <strong>Missing:</strong> {p.match.missing_skills.join(", ")}
              </p>
            )}
          </section>
        )}

        {p.interest && p.interest.conversation.turns.length > 0 && (
          <section className="mt-6">
            <h3 className="text-sm font-semibold mb-2">Outreach conversation</h3>
            <div className="space-y-3">
              {p.interest.conversation.turns.map((t, idx) => (
                <div
                  key={idx}
                  className={`rounded-lg p-3 text-sm ${
                    t.speaker === "recruiter"
                      ? "bg-blue-50 border border-blue-100"
                      : "bg-slate-100 border border-slate-200"
                  }`}
                >
                  <div className="text-xs font-medium uppercase text-slate-500 mb-1">
                    {t.speaker}
                  </div>
                  {t.text}
                </div>
              ))}
            </div>

            {p.interest.signals.length > 0 && (
              <div className="mt-4 text-xs text-slate-600">
                <strong>Signals:</strong> {p.interest.signals.join(" · ")}
              </div>
            )}

            <div className="mt-4">
              <Button onClick={askExplain} disabled={explaining} variant="secondary">
                {explaining ? "Explaining..." : "Explain this conversation"}
              </Button>
              {explanation && (
                <p className="mt-3 text-sm text-slate-700 whitespace-pre-wrap">{explanation}</p>
              )}
            </div>
          </section>
        )}
      </SheetContent>
    </Sheet>
  );
}
