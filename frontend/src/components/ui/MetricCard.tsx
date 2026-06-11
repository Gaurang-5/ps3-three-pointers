"use client";
import React from "react";

interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
  sublabel?: string;
}

export default function MetricCard({
  label,
  value,
  delta,
  deltaType = "neutral",
  sublabel,
}: MetricCardProps) {
  const deltaColor =
    deltaType === "positive"
      ? "text-[var(--gain)]"
      : deltaType === "negative"
        ? "text-[var(--loss)]"
        : "text-[var(--text-secondary)]";

  return (
    <div className="glass-card p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span className="number text-2xl font-semibold text-white tracking-tight">
        {value}
      </span>
      {delta && (
        <span className={`text-xs font-medium ${deltaColor}`}>{delta}</span>
      )}
      {sublabel && (
        <span className="text-[11px] text-[var(--text-tertiary)]">
          {sublabel}
        </span>
      )}
    </div>
  );
}
