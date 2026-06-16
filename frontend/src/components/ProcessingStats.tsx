"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DocumentSummary, QuarantineEntry } from "@/types";

interface ProcessingStatsProps {
  documents: DocumentSummary[];
  quarantine: QuarantineEntry[];
}

const FORMAT_COLORS = [
  "#4f46e5",
  "#6366f1",
  "#818cf8",
  "#a5b4fc",
  "#c7d2fe",
  "#e0e7ff",
];

/**
 * Processing-stats summary: a bar chart of ingested documents grouped by
 * source format, derived from the documents list. Renders an inline legend
 * with totals so the section is informative even before the chart paints.
 */
export default function ProcessingStats({
  documents,
  quarantine,
}: ProcessingStatsProps) {
  const byFormat = new Map<string, number>();
  for (const doc of documents) {
    const key = (doc.format || "other").toLowerCase();
    byFormat.set(key, (byFormat.get(key) ?? 0) + 1);
  }

  const data = Array.from(byFormat.entries())
    .map(([format, count]) => ({ format: format.toUpperCase(), count }))
    .sort((a, b) => b.count - a.count);

  const totalChunks = documents.reduce((acc, d) => acc + d.total_chunks, 0);

  return (
    <div className="card">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">
          Processing summary
        </h2>
        <span className="text-xs text-gray-400">by source format</span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Stat label="Documents" value={documents.length} />
        <Stat label="Total chunks" value={totalChunks} />
        <Stat
          label="Quarantined"
          value={quarantine.length}
          tone={quarantine.length > 0 ? "warn" : "ok"}
        />
      </div>

      {data.length > 0 && (
        <div className="mt-5 h-48 w-full" data-testid="format-chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 4, right: 8, left: -16, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="format"
                tick={{ fontSize: 12, fill: "#64748b" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: "#f8fafc" }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={FORMAT_COLORS[i % FORMAT_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "ok" | "warn";
}) {
  const toneClass =
    tone === "warn"
      ? "text-amber-600"
      : tone === "ok"
        ? "text-emerald-600"
        : "text-gray-900";
  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
      <div className={`text-2xl font-bold ${toneClass}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
