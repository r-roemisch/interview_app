"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Status = "checking" | "online" | "offline";

/** Small indicator so a beginner can see at a glance whether FastAPI is running. */
export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then(() => !cancelled && setStatus("online"))
      .catch(() => !cancelled && setStatus("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  const color =
    status === "online" ? "bg-emerald-500" : status === "offline" ? "bg-red-500" : "bg-zinc-400";
  const label = { checking: "Checking backend", online: "Backend connected", offline: "Backend offline" }[status];
  return (
    <span className="flex items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400" title="FastAPI backend">
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      {/* On a phone only the dot is shown; the label stays for screen readers. */}
      <span className="sr-only sm:not-sr-only">{label}</span>
    </span>
  );
}
