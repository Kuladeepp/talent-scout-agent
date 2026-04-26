"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import type { RankedRow } from "@/lib/types";

type Props = {
  rows: RankedRow[];
  onRowClick: (cid: string) => void;
  selectedCid?: string | null;
  compact?: boolean;
};

function scoreBadge(score: number | null) {
  if (score === null) return <Badge variant="outline">n/a</Badge>;
  const tone =
    score >= 80 ? "bg-emerald-100 text-emerald-800" :
    score >= 60 ? "bg-amber-100 text-amber-800" :
                  "bg-slate-200 text-slate-700";
  return <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${tone}`}>{score}</span>;
}

export function ResultsTable({ rows, onRowClick, selectedCid, compact }: Props) {
  return (
    <Card className="overflow-hidden border-slate-200">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50/80">
              <TableHead className="w-12 text-center">#</TableHead>
              <TableHead>Candidate</TableHead>
              {!compact && <TableHead>Title</TableHead>}
              <TableHead className="w-16 text-center">Match</TableHead>
              <TableHead className="w-16 text-center">Interest</TableHead>
              <TableHead className="w-16 text-center">Final</TableHead>
              {!compact && <TableHead className="min-w-[200px]">Why</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r, i) => {
              const isSelected = r.candidate_id === selectedCid;
              return (
                <TableRow
                  key={r.candidate_id}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-indigo-50 border-l-2 border-l-indigo-500"
                      : "hover:bg-slate-50"
                  }`}
                  onClick={() => onRowClick(r.candidate_id)}
                >
                  <TableCell className="text-center">
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                      i < 3
                        ? "bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
                        : "bg-slate-200 text-slate-600"
                    }`}>
                      {i + 1}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-slate-900">{r.name}</div>
                    {compact && <div className="text-xs text-slate-500 mt-0.5">{r.title}</div>}
                  </TableCell>
                  {!compact && <TableCell className="text-slate-600 text-sm">{r.title}</TableCell>}
                  <TableCell className="text-center">{scoreBadge(r.match_score)}</TableCell>
                  <TableCell className="text-center">{scoreBadge(r.interest_score)}</TableCell>
                  <TableCell className="text-center">{scoreBadge(Math.round(r.final_score))}</TableCell>
                  {!compact && (
                    <TableCell className="text-xs text-slate-500 max-w-xs">
                      <span className="line-clamp-2">{r.match_reasoning}</span>
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
