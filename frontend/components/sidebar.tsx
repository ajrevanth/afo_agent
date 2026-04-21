"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Inbox, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, desc: "Overview & urgent queue" },
  { href: "/documents", label: "Document Inbox", icon: Inbox, desc: "Review & approve" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex items-center gap-2.5 border-b px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-sm">
          <Zap className="h-4.5 w-4.5 text-primary-foreground" />
        </div>
        <div>
          <p className="text-sm font-bold tracking-tight">AFO Agent</p>
          <p className="text-xs text-muted-foreground">Fund of Funds Operations</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {nav.map(({ href, label, icon: Icon, desc }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <div className="min-w-0">
                <p className="font-medium leading-none">{label}</p>
                <p className={cn("mt-0.5 text-xs leading-none truncate", active ? "text-primary-foreground/70" : "text-muted-foreground")}>
                  {desc}
                </p>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="border-t px-5 py-4 space-y-1">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-muted-foreground">Live · polls every 10s</span>
        </div>
        <p className="text-xs text-muted-foreground/60">
          All approvals are logged for audit
        </p>
      </div>
    </aside>
  );
}
