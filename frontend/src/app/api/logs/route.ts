import { NextResponse } from "next/server";
import fs from "fs";
import { findLogFile } from "../_lib/files";

export async function GET() {
  try {
    const filePath = findLogFile("summary_log.json");
    if (!filePath) {
      return NextResponse.json({
        signals_generated: 0,
        trades_executed: 0,
        risk_events: 0,
      });
    }
    const fileContents = fs.readFileSync(filePath, "utf8");
    return NextResponse.json(JSON.parse(fileContents));
  } catch {
    return NextResponse.json({ error: "Failed to read logs" }, { status: 500 });
  }
}
