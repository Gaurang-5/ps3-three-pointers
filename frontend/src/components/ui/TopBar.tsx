"use client";
import { useEffect, useState } from "react";

const tickers = [
  { symbol: "AAPL", change: +2.1 },
  { symbol: "MSFT", change: -0.4 },
  { symbol: "GOOGL", change: +1.8 },
  { symbol: "TSLA", change: -3.2 },
  { symbol: "SPY", change: +0.6 },
  { symbol: "NVDA", change: +4.1 },
  { symbol: "AMZN", change: -0.9 },
  { symbol: "META", change: +1.4 },
];

export default function TopBar({
  portfolioValue,
}: {
  portfolioValue?: number;
}) {
  const [time, setTime] = useState("");
  useEffect(() => {
    const update = () =>
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const formatted = portfolioValue
    ? new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(portfolioValue)
    : "$1,000,000";

  return (
    <header
      className="fixed top-0 right-0 z-40 flex flex-col"
      style={{
        left: 64,
        borderBottom: "1px solid var(--border)",
        background: "rgba(0,0,0,0.9)",
        backdropFilter: "blur(20px)",
      }}
    >
      {/* Scrolling ticker */}
      <div
        className="overflow-hidden whitespace-nowrap py-0.5 px-4"
        style={{
          background: "rgba(0,212,170,0.05)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="inline-flex gap-8 animate-[scroll_30s_linear_infinite]">
          {[...tickers, ...tickers].map((t, i) => (
            <span
              key={i}
              className="number text-[10px]"
              style={{ color: t.change >= 0 ? "var(--gain)" : "var(--loss)" }}
            >
              {t.symbol} {t.change >= 0 ? "+" : ""}
              {t.change}%
            </span>
          ))}
        </div>
      </div>

      {/* Main topbar */}
      <div className="flex items-center justify-between px-6 h-12">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold text-sm">
            HedgeSim Fund
          </span>
          <span style={{ color: "var(--text-tertiary)" }}>·</span>
          <span
            className="flex items-center gap-1.5 text-xs"
            style={{ color: "var(--gain)" }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: "var(--gain)" }}
            />
            LIVE SIMULATION
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div className="number text-sm text-white">{formatted}</div>
          <div
            className="number text-xs"
            style={{ color: "var(--text-secondary)" }}
          >
            {new Date().toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}{" "}
            &nbsp; {time}
          </div>
        </div>
      </div>
    </header>
  );
}
