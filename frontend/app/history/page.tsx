"use client";

import { Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError, type HistoryRow } from "@/lib/api";
import { formatDate, STATUS_LABEL } from "@/lib/labels";
import { ErrorBanner, LinkButton, Page, Spinner, StatusBadge } from "../ui";

// History page: every past Interview. Each row opens the right page for its status.
export default function HistoryPage() {
  const [rows, setRows] = useState<HistoryRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Bumping this counter re-runs the loading effect (used by the Retry button).
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(() => {
    let cancelled = false; // ignore the result if the page unmounted meanwhile
    api
      .listInterviews()
      .then((list) => {
        if (cancelled) return;
        setRows(list);
        setError(null);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Could not load history.");
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  async function remove(row: HistoryRow) {
    if (!window.confirm(`Delete the interview for "${row.title}"? This cannot be undone.`)) return;
    try {
      await api.deleteInterview(row.id);
      setRows((rs) => rs?.filter((r) => r.id !== row.id) ?? null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not delete the interview.");
    }
  }

  const newButton = (
    <LinkButton href="/" variant="primary">
      <Plus className="h-4 w-4" />
      New interview
    </LinkButton>
  );

  return (
    <Page title="History" actions={rows && rows.length > 0 ? newButton : undefined}>
      <div className="space-y-4">
        {error && <ErrorBanner message={error} onRetry={reload} />}
        {!rows && !error && <Spinner label="Loading..." />}

        {rows && rows.length === 0 && (
          <div className="rounded-2xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
            <p className="font-medium">No interviews yet</p>
            <p className="mt-1 mb-5 text-sm text-zinc-500">Your finished and unfinished interviews will be listed here.</p>
            {newButton}
          </div>
        )}

        {rows && rows.length > 0 && (
          <ul className="divide-y divide-zinc-200 overflow-hidden rounded-2xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {rows.map((row) => (
              <li key={row.id} className="flex items-center hover:bg-zinc-50 dark:hover:bg-zinc-900/60">
                {/* In Progress resumes the chat; everything else goes to the Evaluation page,
                    which shows "Re-run" for Evaluation Missing and polls while Judging. */}
                <Link
                  href={row.status === "in_progress" ? `/interviews/${row.id}` : `/interviews/${row.id}/evaluation`}
                  className="flex min-w-0 flex-1 items-center gap-4 px-4 py-3.5 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-indigo-500"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{row.title}</span>
                    <span className="mt-0.5 flex flex-wrap items-center gap-2 text-sm text-zinc-500">
                      {formatDate(row.created_at)}
                      <StatusBadge status={row.status} label={STATUS_LABEL[row.status]} />
                    </span>
                  </span>
                  {row.overall_score !== null && (
                    <span className="text-right">
                      <span className="block text-xl font-semibold tabular-nums">{row.overall_score}</span>
                      <span className="block text-xs text-zinc-500">score</span>
                    </span>
                  )}
                </Link>
                <button
                  onClick={() => void remove(row)}
                  aria-label={`Delete the interview for ${row.title}`}
                  className="mr-2 rounded-lg p-2 text-zinc-400 hover:bg-red-50 hover:text-red-600 focus-visible:outline-2 focus-visible:outline-red-500 dark:hover:bg-red-950/40 dark:hover:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Page>
  );
}
