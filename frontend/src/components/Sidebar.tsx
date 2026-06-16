"use client";

import clsx from "clsx";
import {
  FileText,
  LayoutDashboard,
  Search,
  ShieldAlert,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/ingest", label: "Ingest", icon: Upload },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/search", label: "Search", icon: Search },
  { href: "/quarantine", label: "Quarantine", icon: ShieldAlert },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav className="space-y-1" aria-label="Primary">
      {NAV.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={clsx(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
            isActive(href)
              ? "bg-brand-50 text-brand-700"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
          )}
          aria-current={isActive(href) ? "page" : undefined}
        >
          <Icon className="h-4 w-4 flex-shrink-0" />
          {label}
        </Link>
      ))}
    </nav>
  );
}
