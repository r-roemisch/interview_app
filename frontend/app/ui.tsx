"use client";

// Tiny shared building blocks so the pages stay readable. No component library (spec).

import Link from "next/link";
import type { ComponentProps } from "react";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: "primary" | "secondary" | "danger" }) {
  const base =
    "rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
  const styles = {
    primary: "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300",
    secondary: "border border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800",
    danger: "border border-red-300 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950",
  }[variant];
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}

export function LinkButton({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
    >
      {children}
    </Link>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex items-center justify-between gap-4 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
    >
      <span>{message}</span>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-zinc-500">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-700 dark:border-zinc-700 dark:border-t-zinc-200" />
      {label}
    </span>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-zinc-500">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900";

export function StatusBadge({ status, label }: { status: string; label: string }) {
  const color =
    {
      in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
      judging: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
      completed: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200",
      evaluation_missing: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
    }[status] ?? "bg-zinc-100 text-zinc-800";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>{label}</span>;
}
