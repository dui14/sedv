"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, CircleAlert, History, Loader2 } from "lucide-react";

import { apiRequest, authHeaders } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuditLogItem, AuditLogListResponse, AuthUser } from "../../types";

import styles from "./activity.module.css";

function fmtDate(s: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(s));
}

const RESULT_CLS: Record<string, string> = {
  success: styles.resultSuccess,
  denied: styles.resultDenied,
  error: styles.resultError,
};

export function ActivityScreen() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const PAGE_SIZE = 30;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const t = getAccessToken();
    if (!t) { router.replace("/login"); return; }
    setToken(t);
    load(t, 1);
  }, [router]);

  async function load(t: string, p: number) {
    setLoading(true); setError(null);
    const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE) });
    try {
      const data = await apiRequest<AuditLogListResponse>(`/api/audit-logs/my-activity?${params}`, { headers: authHeaders(t) });
      setLogs(data.items); setTotal(data.total); setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load activity.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.titleRow}>
          <History size={20} className={styles.titleIcon} />
          <div>
            <h1 className={styles.pageTitle}>My Activity</h1>
            <p className={styles.pageSubtitle}>Your personal action history in the vault.</p>
          </div>
        </div>
      </div>

      {error && <div className={styles.errorBanner} role="alert"><CircleAlert size={15} /><span>{error}</span></div>}

      {loading && <div className={styles.loading}><Loader2 size={20} className={styles.spinner} /><span>Loading…</span></div>}

      {!loading && logs.length === 0 && (
        <div className={styles.empty}>
          <History size={32} className={styles.emptyIcon} />
          <p className={styles.emptyTitle}>No activity yet</p>
          <p className={styles.emptyText}>Actions you take will appear here.</p>
        </div>
      )}

      {!loading && logs.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Result</th>
                  <th>Details</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.audit_id}>
                    <td className={styles.tdAction}>{log.action}</td>
                    <td className={styles.tdMuted}>{log.resource_type}{log.resource_id ? ` · ${log.resource_id.slice(0, 8)}…` : ""}</td>
                    <td><span className={RESULT_CLS[log.result] ?? styles.resultError}>{log.result}</span></td>
                    <td className={styles.tdMuted}>{log.reason ?? "—"}</td>
                    <td className={styles.tdMuted}>{fmtDate(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.secondaryButton} type="button" disabled={page <= 1} onClick={() => token && load(token, page - 1)}>
                <ChevronLeft size={14} /> Previous
              </button>
              <span className={styles.pageInfo}>Page {page} of {totalPages}</span>
              <button className={styles.secondaryButton} type="button" disabled={page >= totalPages} onClick={() => token && load(token, page + 1)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
