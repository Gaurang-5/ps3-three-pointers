"use client";
import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: "teal" | "red" | "amber" | "none";
  onClick?: () => void;
}

export default function GlassCard({
  children,
  className = "",
  glow = "none",
  onClick,
}: GlassCardProps) {
  const glowClass = glow !== "none" ? `glow-${glow}` : "";
  return (
    <div
      className={`glass-card ${glowClass} ${className} ${onClick ? "cursor-pointer" : ""}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
