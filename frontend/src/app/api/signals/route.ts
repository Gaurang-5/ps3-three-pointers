import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

function parseCSV(raw: string): Record<string, string>[] {
  const lines = raw.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  return lines.slice(1).map(line => {
    const vals = line.split(',');
    return Object.fromEntries(headers.map((h, i) => [h, (vals[i] || '').trim()]));
  });
}

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'public', 'data', 'signal_heatmap.csv');
    if (!fs.existsSync(filePath)) {
      const signals = ['BUY', 'SELL', 'HOLD'];
      const mock = Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
        ticker: 'Equity',
        signal: signals[Math.floor(Math.random() * 3)],
        composite_score: ((Math.random() - 0.5) * 2).toFixed(3),
      }));
      return NextResponse.json(mock);
    }
    const raw = fs.readFileSync(filePath, 'utf-8');
    return NextResponse.json(parseCSV(raw));
  } catch {
    return NextResponse.json({ error: 'Failed to load signals' }, { status: 500 });
  }
}
