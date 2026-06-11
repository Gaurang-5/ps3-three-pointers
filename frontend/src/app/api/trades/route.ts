import { NextResponse } from "next/server";
import fs from "fs";
import { findLogFile } from "../_lib/files";

function parseJSONL(raw: string) {
  return raw
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

export async function GET() {
  try {
    const filePath = findLogFile("trade_log.jsonl");
    if (!filePath) {
      const mock = Array.from({ length: 15 }, (_, i) => ({
        date: new Date(Date.now() - (14 - i) * 86400000)
          .toISOString()
          .split("T")[0],
        ticker: "Equity",
        action: i % 3 === 0 ? "BUY" : i % 3 === 1 ? "SELL" : "HOLD",
        shares: (Math.random() * 100).toFixed(0),
        price: (95 + Math.random() * 10).toFixed(2),
        costs: {
          commission: (Math.random() * 50).toFixed(2),
          slippage: (Math.random() * 25).toFixed(2),
        },
        portfolio_state: {
          cash: (50000 + Math.random() * 10000).toFixed(2),
          total_value: (1000000 + Math.random() * 50000).toFixed(2),
        },
      }));
      return NextResponse.json(mock);
    }
    const raw = fs.readFileSync(filePath, "utf-8");
    return NextResponse.json(parseJSONL(raw));
  } catch {
    return NextResponse.json(
      { error: "Failed to load trades" },
      { status: 500 },
    );
  }
}
