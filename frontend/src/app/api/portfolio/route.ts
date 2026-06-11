import { NextResponse } from "next/server";
import fs from "fs";
import { findGeneratedFile } from "../_lib/files";

function parseCSV(raw: string): Record<string, string>[] {
  const lines = raw.trim().split("\n");
  const headers = lines[0].split(",").map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const vals = line.split(",");
    return Object.fromEntries(
      headers.map((h, i) => [h, (vals[i] || "").trim()]),
    );
  });
}

export async function GET() {
  try {
    const filePath = findGeneratedFile("portfolio_timeseries.csv");
    if (!filePath) {
      // Return mock timeseries
      const mock = Array.from({ length: 60 }, (_, i) => ({
        Date: new Date(Date.now() - (59 - i) * 86400000)
          .toISOString()
          .split("T")[0],
        Total_Value: (1000000 + (Math.random() - 0.48) * 10000 * i).toFixed(2),
        Cash: "50000",
        Equity_Shares: "0",
        Equity_Price: "100",
      }));
      return NextResponse.json(mock);
    }
    const raw = fs.readFileSync(filePath, "utf-8");
    return NextResponse.json(parseCSV(raw));
  } catch {
    return NextResponse.json(
      { error: "Failed to load portfolio data" },
      { status: 500 },
    );
  }
}
