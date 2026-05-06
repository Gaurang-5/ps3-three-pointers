import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'public', 'data', 'metrics_summary.json');
    if (!fs.existsSync(filePath)) {
      // Return mock data if file doesn't exist yet
      return NextResponse.json({
        'Total Return': 0.005,
        'Sharpe Ratio': -2.6,
        'Sortino Ratio': -3.7,
        'Max Drawdown': -0.196,
        Alpha: -0.0498,
        Beta: -0.003,
      });
    }
    const raw = fs.readFileSync(filePath, 'utf-8');
    return NextResponse.json(JSON.parse(raw));
  } catch (e) {
    return NextResponse.json({ error: 'Failed to load metrics' }, { status: 500 });
  }
}
