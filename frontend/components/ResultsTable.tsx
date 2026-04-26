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
};

function scoreBadge(score: number | null) {
  if (score === null) return <Badge variant="outline">n/a</Badge>;
  const tone =
    score >= 80 ? "bg-emerald-100 text-emerald-800" :
    score >= 60 ? "bg-amber-100 text-amber-800" :
                  "bg-slate-200 text-slate-700";
  return <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${tone}`}>{score}</span>;
}

export function ResultsTable({ rows, onRowClick }: Props) {
  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>Candidate</TableHead>
            <TableHead>Title</TableHead>
            <TableHead className="w-20 text-right">Match</TableHead>
            <TableHead className="w-20 text-right">Interest</TableHead>
            <TableHead className="w-24 text-right">Final</TableHead>
            <TableHead>Why</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r, i) => (
            <TableRow
              key={r.candidate_id}
              className="cursor-pointer hover:bg-indigo-50"
              onClick={() => onRowClick(r.candidate_id)}
            >
              <TableCell>
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-white text-xs font-bold">
                  {i + 1}
                </span>
              </TableCell>
              <TableCell className="font-medium">{r.name}</TableCell>
              <TableCell className="text-slate-600">{r.title}</TableCell>
              <TableCell className="text-right">{scoreBadge(r.match_score)}</TableCell>
              <TableCell className="text-right">{scoreBadge(r.interest_score)}</TableCell>
              <TableCell className="text-right font-semibold">{scoreBadge(Math.round(r.final_score))}</TableCell>
              <TableCell className="text-sm text-slate-600 max-w-md truncate">
                {r.match_reasoning}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}
