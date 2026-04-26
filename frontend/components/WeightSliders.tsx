"use client";

import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import type { Weights } from "@/lib/types";

type Props = {
  weights: Weights;
  onChange: (w: Weights) => void;
};

export function WeightSliders({ weights, onChange }: Props) {
  const safeMatch = Number.isFinite(weights.match) ? weights.match : 0.6;
  const safeInterest = Number.isFinite(weights.interest) ? weights.interest : 0.4;

  const setMatch = (raw: unknown) => {
    const n = typeof raw === "number" && Number.isFinite(raw) ? raw : Math.round(safeMatch * 100);
    const m = Math.round(n) / 100;
    onChange({ match: m, interest: Math.round((1 - m) * 100) / 100 });
  };

  return (
    <Card className="p-4 space-y-3 shadow-sm">
      <div className="text-sm font-semibold text-slate-800">Score weighting</div>
      <div>
        <div className="flex justify-between text-xs text-slate-600 mb-2">
          <span>Match: <b>{Math.round(safeMatch * 100)}%</b></span>
          <span>Interest: <b>{Math.round(safeInterest * 100)}%</b></span>
        </div>
        <Slider
          value={[Math.round(safeMatch * 100)]}
          onValueChange={(v) => {
            const arr = Array.isArray(v) ? v : [];
            setMatch(arr[0]);
          }}
          min={0}
          max={100}
          step={5}
        />
      </div>
      <p className="text-xs text-slate-500">
        Drag to re-rank live without re-running the pipeline.
      </p>
    </Card>
  );
}
