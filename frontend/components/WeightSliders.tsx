"use client";

import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import type { Weights } from "@/lib/types";

type Props = {
  weights: Weights;
  onChange: (w: Weights) => void;
};

export function WeightSliders({ weights, onChange }: Props) {
  const setMatch = (v: number) => {
    const m = Math.round(v) / 100;
    onChange({ match: m, interest: Math.round((1 - m) * 100) / 100 });
  };

  return (
    <Card className="p-4 space-y-3">
      <div className="text-sm font-medium">Score weighting</div>
      <div>
        <div className="flex justify-between text-xs text-slate-600 mb-1">
          <span>Match: {Math.round(weights.match * 100)}%</span>
          <span>Interest: {Math.round(weights.interest * 100)}%</span>
        </div>
        <Slider
          value={[Math.round(weights.match * 100)]}
          onValueChange={(v) => setMatch((v as number[])[0])}
          min={0}
          max={100}
          step={5}
        />
      </div>
      <p className="text-xs text-slate-500">
        Move the slider to re-rank live without re-running the pipeline.
      </p>
    </Card>
  );
}
