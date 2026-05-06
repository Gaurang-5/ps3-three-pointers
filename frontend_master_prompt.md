# FRONTEND MASTER PROMPT
## Hedge Fund Risk Modeling — Trading Dashboard
### Stack: Next.js 14 + Three.js + Tailwind CSS

---

## ROLE & VISION

You are a senior UI/UX engineer building a **premium trading dashboard** for a hedge fund simulation system. The aesthetic must feel like **Apple meets Bloomberg Terminal** — obsessively clean, dark-first, with purposeful 3D moments powered by Three.js. Every pixel earns its place. No decoration for decoration's sake.

**Mood board in words:**
- Apple's spatial computing UI (visionOS vibes) — glass, depth, restraint
- Bloomberg Terminal's data density — numbers everywhere, but readable
- A trader's second monitor — live, tense, precise
- Three.js 3D only where it adds meaning: portfolio globe, risk sphere, 3D candlestick chart

---

## TECH STACK

```
Framework:     Next.js 14 (App Router)
3D:            Three.js (r158+) — direct, no react-three-fiber
Charts:        Recharts for 2D data charts
Styling:       Tailwind CSS + CSS custom properties
Fonts:         SF Pro Display (via system-ui) + JetBrains Mono for numbers
Animation:     Framer Motion for page transitions + GSAP for 3D camera moves
State:         Zustand (lightweight global store)
Data:          Reads from the backend's exported JSON/CSV files via Next.js API routes
Icons:         Lucide React
```

**3D approach — Three.js directly (no react-three-fiber):**
- Mount Three.js scenes in `useEffect` with a `<canvas ref>` inside React components
- Animate with `requestAnimationFrame` loops
- Clean up renderer and geometries on component unmount
- Keep 3D scenes self-contained in `/components/three/` folder

---

## COLOR SYSTEM

```css
/* Dark theme (default) */
--bg-primary:    #000000;        /* Pure black — like macOS menu bar */
--bg-secondary:  #0A0A0A;        /* Cards, panels */
--bg-tertiary:   #111111;        /* Elevated surfaces */
--bg-glass:      rgba(255,255,255,0.04);  /* Glass cards */
--border:        rgba(255,255,255,0.08);  /* Subtle borders */
--border-bright: rgba(255,255,255,0.15);  /* Hover borders */

/* Text */
--text-primary:   #FFFFFF;
--text-secondary: #8A8A8E;       /* Apple's secondary label gray */
--text-tertiary:  #48484A;

/* Accent — one color only */
--accent:        #00D4AA;        /* Teal/green — "in the money" color */
--accent-dim:    rgba(0, 212, 170, 0.15);

/* Semantic */
--gain:  #34C759;   /* Apple green */
--loss:  #FF3B30;   /* Apple red */
--warn:  #FF9F0A;   /* Apple amber */

/* 3D atmosphere */
--glow-teal:  rgba(0, 212, 170, 0.3);
--glow-blue:  rgba(10, 132, 255, 0.2);
```

---

## TYPOGRAPHY RULES

```css
/* Numbers always in monospace — they must align */
.number, .price, .metric { font-family: 'JetBrains Mono', monospace; }

/* Headings — system San Francisco */
h1 { font-size: 28px; font-weight: 600; letter-spacing: -0.5px; }
h2 { font-size: 20px; font-weight: 500; letter-spacing: -0.3px; }

/* Labels — uppercase micro */
.label { font-size: 10px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-secondary); }

/* Body */
p { font-size: 14px; line-height: 1.6; color: var(--text-secondary); }
```

---

## PROJECT STRUCTURE

```
/app
  /page.tsx                    → Redirect to /dashboard
  /dashboard/page.tsx          → Main overview
  /portfolio/page.tsx          → Portfolio deep-dive
  /risk/page.tsx               → Risk management center
  /signals/page.tsx            → Signal heatmap + trade log
  /performance/page.tsx        → Metrics + Sharpe/Alpha/Beta
  /layout.tsx                  → Root layout with sidebar

/components
  /three
    PortfolioGlobe.tsx         → 3D globe with asset nodes
    RiskSphere.tsx             → 3D pulsing risk indicator
    CandlestickChart3D.tsx     → 3D candlestick (Three.js)
    MarketParticles.tsx        → Ambient background particle field
  /charts
    PortfolioValueChart.tsx    → Recharts area chart
    AllocationDonut.tsx        → Recharts donut
    DrawdownChart.tsx          → Recharts area (negative zone)
    SignalHeatmap.tsx          → CSS grid heatmap
    RollingMetricsChart.tsx    → Multi-line Recharts
  /ui
    MetricCard.tsx             → Stat card with delta
    TradeRow.tsx               → Single trade log row
    RiskGauge.tsx              → SVG arc gauge
    Ticker.tsx                 → Live-style scrolling ticker
    GlassCard.tsx              → Reusable glass-morphism card
    Sidebar.tsx                → Navigation
    TopBar.tsx                 → Header with portfolio summary

/lib
  /data.ts                     → Reads JSON/CSV from backend outputs
  /formatters.ts               → Currency, %, date formatters
  /store.ts                    → Zustand global state

/public/data                   → Backend output files dropped here
  portfolio_timeseries.csv
  trade_log.csv
  asset_allocations.csv
  metrics_summary.json
  signal_heatmap.csv
```

---

## PAGE 1 — DASHBOARD (Main Overview)

**Layout:** Full-screen dark canvas. Left: fixed sidebar (64px). Right: main content area.

### Top Section — Hero 3D + Key Numbers

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   PORTFOLIO VALUE          [3D RiskSphere]          │
│   $1,247,832.40                floating right       │
│   +$247,832 (+24.78%)                               │
│                                                     │
│   [Sharpe: 1.84]  [VaR: 2.3%]  [Drawdown: -8.2%]  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**3D Component — `RiskSphere.tsx`:**
- A Three.js sphere, ~200px, positioned top-right of the hero
- Texture: wireframe icosphere with glowing nodes at vertices
- Color shifts based on current VaR: green (low risk) → amber (medium) → red (high)
- Slowly rotates on Y axis
- On hover: camera zooms in slightly (GSAP tween), sphere reveals inner concentric rings
- Ambient point light + directional light for depth
- `renderer.shadowMap.enabled = true`

```typescript
// Three.js setup pattern for RiskSphere
useEffect(() => {
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100)
  camera.position.z = 3

  const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: true, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(200, 200)

  // Icosphere wireframe
  const geo = new THREE.IcosahedronGeometry(1, 3)
  const mat = new THREE.MeshBasicMaterial({ color: getRiskColor(varValue), wireframe: true, transparent: true, opacity: 0.6 })
  const sphere = new THREE.Mesh(geo, mat)
  scene.add(sphere)

  // Inner glow sphere
  const innerGeo = new THREE.SphereGeometry(0.85, 32, 32)
  const innerMat = new THREE.MeshBasicMaterial({ color: getRiskColor(varValue), transparent: true, opacity: 0.05 })
  scene.add(new THREE.Mesh(innerGeo, innerMat))

  // Animate
  let raf: number
  const animate = () => {
    raf = requestAnimationFrame(animate)
    sphere.rotation.y += 0.003
    sphere.rotation.x += 0.001
    renderer.render(scene, camera)
  }
  animate()

  return () => { cancelAnimationFrame(raf); renderer.dispose() }
}, [varValue])
```

### Middle Section — Portfolio Value Chart

- Full-width Recharts `AreaChart`
- Dark background, `--accent` colored area fill with gradient from `rgba(0,212,170,0.3)` to transparent
- Benchmark line overlaid in `--text-tertiary` dashed
- X-axis: dates, Y-axis: dollar values in JetBrains Mono
- Hover tooltip: glass card showing date, portfolio value, benchmark value, daily return
- Time range selector pills: 1W / 1M / 3M / 6M / ALL (filters the data)

### Bottom Section — 4 Mini Cards in a Row

```
[Active Positions]  [Today's Trades]  [Best Performer]  [Risk Status]
     12 stocks           8 executed       AAPL +4.2%       ● NORMAL
```

Each card: glass-morphism (`backdrop-filter: blur(20px)`) with `border: 1px solid var(--border)`

---

## PAGE 2 — PORTFOLIO (Deep Dive)

### Left Half — `PortfolioGlobe.tsx`

**3D Component:** A globe made of particles + glowing asset location nodes.

```typescript
// PortfolioGlobe pattern
// Each asset gets a 3D node positioned on a sphere surface
// Node size = position size (bigger allocation = bigger node)
// Node color = green if profitable, red if loss, white if flat
// Hovering a node shows a floating label with ticker + P&L

const phi = Math.acos(-1 + (2 * i) / numAssets)  // fibonacci sphere distribution
const theta = Math.sqrt(numAssets * Math.PI) * phi
const x = Math.cos(theta) * Math.sin(phi)
const y = Math.sin(theta) * Math.sin(phi)
const z = Math.cos(phi)
```

- Globe continuously rotates slowly
- Mouse drag: OrbitControls-like rotation (implement manually, no extra library)
- Thin latitude/longitude grid lines in `rgba(255,255,255,0.05)`
- Click a node: sidebar panel slides in with that stock's details

### Right Half — Allocation Breakdown

- Recharts `PieChart` (donut) showing current weights
- Below: sortable table of all positions
  - Columns: Ticker | Shares | Avg Cost | Current Price | P&L | Weight | Signal

---

## PAGE 3 — RISK MANAGEMENT CENTER

### Hero — 3D Risk Visualization

**`CandlestickChart3D.tsx`** — Three.js 3D bar chart:
- Each day's OHLCV data rendered as a 3D candlestick
- Green `BoxGeometry` for up days, red for down days
- Camera positioned at 45° angle looking down the time axis
- Mouse scroll: zoom in/out (camera dolly)
- Clicking a candle: highlights it and shows tooltip with exact OHLC values

```typescript
// 3D Candlestick construction
candles.forEach((day, i) => {
  const isUp = day.close >= day.open
  const bodyHeight = Math.abs(day.close - day.open) * scale
  const bodyGeo = new THREE.BoxGeometry(0.6, bodyHeight, 0.6)
  const bodyMat = new THREE.MeshStandardMaterial({
    color: isUp ? 0x34C759 : 0xFF3B30,
    roughness: 0.3,
    metalness: 0.6
  })
  const body = new THREE.Mesh(bodyGeo, bodyMat)
  body.position.set(i * 1.2, (day.open + day.close) / 2 * scale, 0)
  scene.add(body)

  // Wick
  const wickGeo = new THREE.BoxGeometry(0.05, (day.high - day.low) * scale, 0.05)
  const wick = new THREE.Mesh(wickGeo, bodyMat)
  wick.position.set(i * 1.2, (day.high + day.low) / 2 * scale, 0)
  scene.add(wick)
})
```

### Risk Gauges Row

Three SVG arc gauges side by side:
1. **VaR Gauge** — 0 to 5%, needle pointing at current VaR
2. **Drawdown Gauge** — 0 to -30%, needle at current drawdown
3. **Volatility Gauge** — 0 to 50% annualized

Each gauge: dark arc background + colored filled arc + monospace number in center

### Risk Events Log

Timeline of risk breach events logged by the backend:
```
● 2024-03-15   VaR Breach — 3.8% (limit: 3.0%)      [FLAGGED]
● 2024-02-28   Drawdown Alert — -12.4%               [RESOLVED]
● 2024-01-10   Capital Low — Cash < 5% threshold     [RESOLVED]
```

---

## PAGE 4 — SIGNALS

### Signal Heatmap (Full Width)

- CSS Grid: rows = tickers, columns = dates (last 60 days)
- Each cell: colored square
  - `--gain` = BUY signal
  - `--loss` = SELL signal
  - `var(--text-tertiary)` = HOLD
  - Intensity: opacity maps to composite score magnitude
- Hover on cell: tooltip showing exact score + all factor values that drove it
- X-axis: dates, Y-axis: ticker names in monospace

```typescript
// Heatmap cell rendering
<div
  key={`${ticker}-${date}`}
  className="cell"
  style={{
    backgroundColor: signal === 'BUY' ? `rgba(52,199,89,${score})` :
                     signal === 'SELL' ? `rgba(255,59,48,${Math.abs(score)})` :
                     'rgba(72,72,74,0.3)',
    width: 14, height: 14, borderRadius: 2
  }}
  title={`${ticker} | ${date} | Score: ${score.toFixed(2)}`}
/>
```

### Trade Log Table

Sortable, filterable table of all executed trades:
- Filter by: ticker, action (BUY/SELL), date range
- Columns: Date | Ticker | Action | Shares | Price | Value | Commission | Slippage | Reason
- Row color: BUY rows have subtle green left border, SELL rows red
- Export to CSV button

---

## PAGE 5 — PERFORMANCE

### Hero Metrics — 6 Large Cards

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Sharpe Ratio │ │    Alpha     │ │     Beta     │
│    1.84      │ │   +6.3%     │ │    0.72      │
│ Annualized   │ │  vs SPY     │ │ Market corr  │
└──────────────┘ └──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Ann. Return │ │ Ann. Volat.  │ │ Max Drawdown │
│   +22.4%     │ │   12.1%     │ │   -8.2%      │
│ vs 10.2% mkt │ │  controlled │ │  peak-trough │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Rolling Metrics Chart

Multi-line Recharts `LineChart`:
- Line 1: Rolling 30-day Sharpe (teal)
- Line 2: Rolling VaR (amber)
- Line 3: Rolling Drawdown (red, always negative, plotted on secondary axis)
- Hover shows all three values on the same date

### Portfolio vs Benchmark Chart

Two overlaid `AreaChart` series:
- Our portfolio: filled teal area
- Benchmark (SPY): dashed white line, no fill
- Annotated with key events (rebalance dates, risk breaches)

---

## SIDEBAR NAVIGATION

```
┌──┐
│  │  ← Logo / Fund name (small, elegant)
│  │
│ ⊡ │  Dashboard
│ ◎ │  Portfolio
│ ⚠ │  Risk
│ ≋ │  Signals
│ ↗ │  Performance
│   │
│ ⚙ │  Settings (bottom)
└──┘
```

- Width: 64px collapsed, 220px expanded on hover
- Active item: `--accent` left border 2px + tinted background
- Transitions: smooth 200ms width expand
- On mobile: bottom tab bar instead

---

## TOP BAR

```
[Fund Name]  ●  LIVE SIMULATION     |  Portfolio: $1,247,832  +24.78%  |  [Date] [Time]
```

- Portfolio value updates on page focus (re-reads data)
- Subtle pulsing green dot for "live" status
- Scrolling ticker at very top (1px tall): AAPL +2.1% | MSFT -0.4% | GOOGL +1.8% | ...

---

## 3D BACKGROUND — `MarketParticles.tsx`

Ambient background across all pages (positioned fixed, z-index -1):

```typescript
// 3,000 particles floating slowly
// They represent "market data" — abstract but atmospheric
const particles = new THREE.BufferGeometry()
const positions = new Float32Array(3000 * 3)
for (let i = 0; i < 9000; i++) {
  positions[i] = (Math.random() - 0.5) * 80
}
particles.setAttribute('position', new THREE.BufferAttribute(positions, 3))

const mat = new THREE.PointsMaterial({
  size: 0.04,
  color: 0x00D4AA,
  transparent: true,
  opacity: 0.2,
  blending: THREE.AdditiveBlending
})

const points = new THREE.Points(particles, mat)
scene.add(points)

// Drift slowly
const animate = () => {
  points.rotation.y += 0.0001
  points.rotation.x += 0.00005
  renderer.render(scene, camera)
  requestAnimationFrame(animate)
}
```

Keep this VERY subtle — opacity 0.15-0.2 max. It should feel like depth, not distraction.

---

## GLASS CARD COMPONENT

Reusable component used everywhere:

```tsx
// components/ui/GlassCard.tsx
interface GlassCardProps {
  children: React.ReactNode
  className?: string
  glow?: 'teal' | 'red' | 'amber' | 'none'
  onClick?: () => void
}

// CSS
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.glass-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
}
.glass-card.glow-teal {
  box-shadow: 0 0 40px rgba(0, 212, 170, 0.08);
}
.glass-card.glow-red {
  box-shadow: 0 0 40px rgba(255, 59, 48, 0.1);
}
```

---

## METRIC CARD COMPONENT

```tsx
// components/ui/MetricCard.tsx
interface MetricCardProps {
  label: string
  value: string          // formatted: "$1,247,832" or "1.84" or "+24.78%"
  delta?: string         // "+$247,832" or "+2.3pp"
  deltaType?: 'positive' | 'negative' | 'neutral'
  sublabel?: string      // "vs SPY benchmark"
}

// Visual: label (10px uppercase gray) → value (28px mono white) → delta badge → sublabel
```

---

## DATA INTEGRATION

```typescript
// lib/data.ts
// Next.js API routes read the backend's output files

// GET /api/portfolio → reads portfolio_timeseries.csv
// GET /api/trades → reads trade_log.csv
// GET /api/allocations → reads asset_allocations.csv
// GET /api/metrics → reads metrics_summary.json
// GET /api/signals → reads signal_heatmap.csv

// Client-side: use SWR for data fetching with auto-refresh
import useSWR from 'swr'
const { data: metrics } = useSWR('/api/metrics', fetcher, { refreshInterval: 30000 })
```

---

## ANIMATION GUIDELINES

**Page transitions (Framer Motion):**
```tsx
// Wrap each page content in:
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
>
```

**Number counters:**
- On mount, animate metric card numbers from 0 to their value
- Use GSAP `gsap.to({ val: 0 }, { val: target, duration: 1.2, ease: 'power2.out', onUpdate })`

**3D camera tweens (GSAP):**
```typescript
gsap.to(camera.position, {
  z: 2.5,
  duration: 0.6,
  ease: 'power2.out'
})
```

**Keep it restrained:**
- No bouncing, no elastic, no spring
- One animation per user action — not cascading sequences
- Hover: 150ms transitions only. Clicks: 300ms max.

---

## RESPONSIVE BEHAVIOR

- Desktop (1280px+): Full layout as described above
- Tablet (768px–1280px): Sidebar collapses to icons only, charts stack
- Mobile (< 768px): Bottom nav, charts scroll horizontally, 3D disabled (show static SVG fallback)

---

## WHAT NOT TO DO

- No gradients except as chart fills (never on cards or backgrounds)
- No neon glow — the `--accent` teal is used sparingly, not everywhere
- No animations that run continuously on a card (only on 3D elements)
- No white backgrounds — everything is dark or transparent
- No rounded corners bigger than 20px (Apple uses restraint)
- No "crypto dashboard" aesthetic — this is institutional, not retail
- Never put too much information on one chart — split into separate charts
- Don't use any charting library other than Recharts and Three.js

---

## IMPLEMENTATION ORDER

Build in this sequence:

1. **Setup** — Next.js 14, Tailwind, install deps (`three`, `recharts`, `framer-motion`, `gsap`, `zustand`, `lucide-react`, `swr`)
2. **Layout** — `layout.tsx` with Sidebar + TopBar (static data first)
3. **GlassCard + MetricCard** — the reusable building blocks
4. **Dashboard page** — wire up all charts with static mock data
5. **3D: RiskSphere** — integrate into Dashboard hero
6. **3D: MarketParticles** — global background
7. **Portfolio page** — PortfolioGlobe + allocation table
8. **3D: CandlestickChart3D** — Risk page hero
9. **Risk + Signals + Performance pages** — complete the remaining pages
10. **Data integration** — swap mock data for real API routes reading backend CSVs
11. **Polish** — Framer Motion transitions, GSAP number counters, responsive

---

## DELIVERABLE CHECKLIST

- [ ] All 5 pages built and navigable
- [ ] 3 Three.js 3D components: RiskSphere, PortfolioGlobe, CandlestickChart3D
- [ ] 1 ambient Three.js background: MarketParticles
- [ ] All charts connected to real backend data via API routes
- [ ] Dark theme throughout — no light mode needed
- [ ] JetBrains Mono for all numbers
- [ ] Glass card style consistent across all pages
- [ ] Framer Motion page transitions working
- [ ] Mobile responsive (bottom nav, 3D disabled)
- [ ] No console errors, no layout overflow on 1440px screen

---

*Frontend prompt for Code2Create Round 3 — Hedge Fund Risk Modeling Dashboard*
*Stack: Next.js 14 + Three.js + Recharts + Framer Motion + Tailwind*
