"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/today", label: "Today" },
  { href: "/wardrobe", label: "Wardrobe" },
  { href: "/stylist", label: "Stylist" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Profile" },
] as const;

export function TabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-line bg-bg-elevated pb-[env(safe-area-inset-bottom)]">
      {TABS.map((tab) => {
        const active = pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex-1 py-3 text-center font-mono text-[10px] uppercase tracking-wide ${
              active ? "text-accent" : "text-ink-faint"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
