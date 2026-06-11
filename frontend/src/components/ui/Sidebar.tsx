"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PieChart,
  ShieldAlert,
  Activity,
  TrendingUp,
  Settings,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/portfolio", icon: PieChart, label: "Portfolio" },
  { href: "/risk", icon: ShieldAlert, label: "Risk" },
  { href: "/signals", icon: Activity, label: "Signals" },
  { href: "/performance", icon: TrendingUp, label: "Performance" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(false);

  return (
    <aside
      className="fixed left-0 top-0 h-full z-50 flex flex-col items-start pt-6 pb-6 transition-all duration-200"
      style={{
        width: expanded ? 220 : 64,
        background: "rgba(10,10,10,0.95)",
        backdropFilter: "blur(20px)",
        borderRight: "1px solid var(--border)",
      }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 mb-8 overflow-hidden w-full">
        <div
          className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center"
          style={{
            background: "var(--accent-dim)",
            border: "1px solid var(--accent)",
          }}
        >
          <span className="text-[var(--accent)] font-bold text-sm">H</span>
        </div>
        {expanded && (
          <span className="text-white text-sm font-semibold whitespace-nowrap">
            HedgeSim
          </span>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col gap-1 w-full flex-1 px-2">
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 overflow-hidden"
              style={{
                color: active ? "var(--accent)" : "var(--text-secondary)",
                background: active ? "var(--accent-dim)" : "transparent",
                borderLeft: active
                  ? "2px solid var(--accent)"
                  : "2px solid transparent",
              }}
            >
              <Icon size={18} className="flex-shrink-0" />
              {expanded && (
                <span className="text-sm whitespace-nowrap">{label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Settings */}
      <div className="px-2 w-full">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl overflow-hidden"
          style={{ color: "var(--text-tertiary)" }}
        >
          <Settings size={18} className="flex-shrink-0" />
          {expanded && (
            <span className="text-sm whitespace-nowrap">Settings</span>
          )}
        </Link>
      </div>
    </aside>
  );
}
