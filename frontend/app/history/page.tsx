"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type HistoryRow } from "@/lib/api";
import { formatDate, STATUS_LABEL } from "@/lib/labels";
import { Button, ErrorBanner, LinkButton, Spinner, StatusBadge } from "../ui";

// History page: every past Interview. Row click opens the right page for its status.
export default function HistoryPage() {
  const router = useRouter();
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

  function open(row: HistoryRow) {
    // In Progress resumes the chat; everything else goes to the Evaluation page,
    // which shows "Re-run" for Evaluation Missing and polls while Judging.
    router.push(row.status === "in_progress" ? `/interviews/${row.id}` : `/interviews/${row.id}/evaluation`);
  }

  async function remove(row: HistoryRow) {
    if (!window.confirm(`Delete the interview for "${row.title}"? This cannot be undone.`)) return;
    try {
      await api.deleteInterview(row.id);
      setRows((rs) => rs?.filter((r) => r.id !== row.id) ?? null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not delete the interview.");
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">History</h1>
        <LinkButton href="/">New interview</LinkButton>
      </header>

      {error && <ErrorBanner message={error} onRetry={reload} />}
      {!rows && !error && <Spinner label="Loading..." />}
      {rows && rows.length === 0 && <p className="text-sm text-zinc-500">No interviews yet.</p>}

      {rows && rows.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-zinc-500">
            <tr>
              <th className="py-2">Job</th>
              <th className="py-2">Date</th>
              <th className="py-2">Status</th>
              <th className="py-2 text-right">Score</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className="cursor-pointer border-t border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                onClick={() => open(row)}
              >
                <td className="py-3 font-medium">{row.title}</td>
                <td className="py-3 text-zinc-500">{formatDate(row.created_at)}</td>
                <td className="py-3">
                  <StatusBadge status={row.status} label={STATUS_LABEL[row.status]} />
                </td>
                <td className="py-3 text-right tabular-nums">{row.overall_score ?? "–"}</td>
                <td className="py-3 text-right">
                  <Button
                    variant="danger"
                    onClick={(e) => {
                      e.stopPropagation(); // don't also open the row
                      void remove(row);
                    }}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
