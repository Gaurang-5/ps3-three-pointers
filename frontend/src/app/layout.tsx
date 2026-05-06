import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/ui/Sidebar';
import TopBar from '@/components/ui/TopBar';

export const metadata: Metadata = {
  title: 'HedgeSim — Hedge Fund Trading Dashboard',
  description: 'Production-grade hedge fund risk modeling and semi-automated trading dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
        <Sidebar />
        <TopBar />
        <main
          style={{
            marginLeft: 64,
            paddingTop: 72,
            minHeight: '100vh',
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
