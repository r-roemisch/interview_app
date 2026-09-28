"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BackendStatus } from "./backend-status";

const links = [
  { href: "/", label: "New interview" },
  { href: "/history", label: "History" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="shrink-0 border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <nav className="flex items-center gap-5 px-4 py-3 text-sm sm:gap-6">
        <Link href="/" className="font-semibold">
          Interview Practice
        </Link>
        {links.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={
                active
                  ? "font-medium text-zinc-900 dark:text-zinc-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              }
            >
              {label}
            </Link>
          );
        })}
        <span className="ml-auto">
          <BackendStatus />
        </span>
      </nav>
    </header>
  );
}
