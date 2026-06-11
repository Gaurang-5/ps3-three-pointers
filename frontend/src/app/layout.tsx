import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/ui/Sidebar";
import TopBar from "@/components/ui/TopBar";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "HedgeSim — Hedge Fund Trading Dashboard",
  description:
    "Production-grade hedge fund risk modeling and semi-automated trading dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${jetbrainsMono.variable}`}>
      <body style={{ background: "var(--bg-primary)", minHeight: "100vh" }}>
        <Sidebar />
        <TopBar />
        <main
          style={{
            marginLeft: 64,
            paddingTop: 72,
            minHeight: "100vh",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
