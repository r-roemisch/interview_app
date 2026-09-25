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
    <header className="border-b border-zinc-200 dark:border-zinc-800">
      <nav className="mx-auto flex w-full max-w-3xl items-center gap-6 px-4 py-3">
        <span className="font-semibold">Interview Practice</span>
        {links.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={active ? "font-medium underline underline-offset-4" : "text-zinc-600 hover:underline dark:text-zinc-400"}
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
