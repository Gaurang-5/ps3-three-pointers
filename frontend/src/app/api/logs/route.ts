import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), '..', 'logs', 'summary_log.json');
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ 
        signals_generated: 0, 
        trades_executed: 0, 
        risk_events: 0 
      });
    }
    const fileContents = fs.readFileSync(filePath, 'utf8');
    return NextResponse.json(JSON.parse(fileContents));
  } catch (error) {
    return NextResponse.json({ error: 'Failed to read logs' }, { status: 500 });
  }
}
