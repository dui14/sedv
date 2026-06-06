"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3, ChevronLeft, ChevronRight, CircleAlert,
  Filter, Loader2, RefreshCw, Search,
} from "lucide-react";

import { apiRequest, authHeaders } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuditLogItem, AuditLogListResponse, AuthUser } from "../../types";

import styles from "./audit-log-screen.module.css";

function fmtDate(s: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(s));
}

function resourceLabel(row: AuditLogItem) {
  return row.resource_id
    ? `${row.resource_type} · ${row.resource_id.slice(0, 10)}…`
    : row.resource_type;
}

const RESULT_CLS: Record<string, string> = {
  success: styles.resultSuccess,
  denied: styles.resultDenied,
  error: styles.resultError,
};

export function AuditLogScreen() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [rows, setRows] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [resultFilter, setResultFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const PAGE_SIZE = 30;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const t = getAccessToken();
    if (!t) { router.replace("/login"); return; }
    setToken(t);
    apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(t) })
      .then((u) => { setUser(u); return load(t, 1, { search: "", action: "", result: "", actor: "" }); })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function load(t: string, p: number, filters: { search: string; action: string; result: string; actor: string }) {
    setLoading(true); setError(null);
    const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE) });
    if (filters.search.trim()) params.set("search", filters.search.trim());
    if (filters.action.trim()) params.set("action", filters.action.trim());
    if (filters.result.trim()) params.set("result", filters.result.trim());
    if (filters.actor.trim()) params.set("actor", filters.actor.trim());
    try {
      const data = await apiRequest<AuditLogListResponse>(`/api/audit-logs?${params}`, { headers: authHeaders(t) });
      setRows(data.items); setTotal(data.total); setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load audit log.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) return;
    void load(token, 1, { search, action: actionFilter, result: resultFilter, actor: actorFilter });
  }

  function clearFilters() {
    setSearch(""); setActionFilter(""); setResultFilter(""); setActorFilter("");
    if (token) void load(token, 1, { search: "", action: "", result: "", actor: "" });
  }

  const isAdmin = user?.role === "admin";

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.titleRow}>
          <BarChart3 size={20} className={styles.titleIcon} />
          <div>
            <h1 className={styles.pageTitle}>Audit Log</h1>
            <p className={styles.pageSubtitle}>
              {isAdmin ? "Full audit trail across all users and vaults." : "General vault activity within your scope."}
            </p>
          </div>
        </div>
        <button className={styles.secondaryButton} type="button" onClick={() => token && load(token, page, { search, action: actionFilter, result: resultFilter, actor: actorFilter })}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error && <div className={styles.errorBanner} role="alert"><CircleAlert size={15} /><span>{error}</span></div>}

      <form className={styles.filters} onSubmit={handleSubmit}>
        <div className={styles.filterRow}>
          <div className={styles.searchWrap}>
            <Search size={14} className={styles.filterIcon} />
            <input className={styles.filterInput} type="search" placeholder="Search action, resource, reason…" value={search} onChange={(e) => setSearch(e.target.value)} disabled={loading} />
          </div>
          <div className={styles.searchWrap}>
            <Filter size={14} className={styles.filterIcon} />
            <input className={styles.filterInput} type="text" placeholder="Action (e.g. upload)" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} disabled={loading} />
          </div>
          <div className={styles.searchWrap}>
            <input className={styles.filterInput} type="text" placeholder="Result: success, denied, error" value={resultFilter} onChange={(e) => setResultFilter(e.target.value)} disabled={loading} style={{ paddingLeft: 12 }} />
          </div>
          {isAdmin && (
            <div className={styles.searchWrap}>
              <input className={styles.filterInput} type="text" placeholder="Actor user ID" value={actorFilter} onChange={(e) => setActorFilter(e.target.value)} disabled={loading} style={{ paddingLeft: 12 }} />
            </div>
          )}
        </div>
        <div className={styles.filterActions}>
          <button className={styles.secondaryButton} type="button" onClick={clearFilters}>Clear</button>
          <button className={styles.primaryButton} type="submit" disabled={loading}>Apply</button>
        </div>
      </form>

      {loading && <div className={styles.loading}><Loader2 size={20} className={styles.spinner} /><span>Loading…</span></div>}

      {!loading && rows.length === 0 && (
        <div className={styles.empty}>
          <p className={styles.emptyTitle}>No audit events found</p>
          <p className={styles.emptyText}>Try clearing filters to see all events.</p>
          <button className={styles.secondaryButton} type="button" onClick={clearFilters}>Clear filters</button>
        </div>
      )}

      {!loading && rows.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Result</th>
                  <th>Details</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.audit_id}>
                    <td className={styles.tdBold}>
                      <span>{row.actor_name}</span>
                      {row.actor_floor_name && (
                        <span className={styles.actorFloorTag}>{row.actor_floor_name}</span>
                      )}
                      {row.actor_department && (
                        <span className={styles.actorDeptTag}>{row.actor_department}</span>
                      )}
                    </td>
                    <td className={styles.tdMono}>{row.action}</td>
                    <td className={styles.tdMono}>{resourceLabel(row)}</td>
                    <td><span className={RESULT_CLS[row.result] ?? styles.resultError}>{row.result}</span></td>
                    <td className={styles.tdMuted}>{row.reason ?? "—"}</td>
                    <td className={styles.tdMuted}>{fmtDate(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationBar}>
            <button className={styles.secondaryButton} type="button" disabled={page <= 1} onClick={() => token && load(token, page - 1, { search, action: actionFilter, result: resultFilter, actor: actorFilter })}>
              <ChevronLeft size={14} /> Previous
            </button>
            <span className={styles.pageInfo}>Page {page} of {totalPages} · {total} events</span>
            <button className={styles.secondaryButton} type="button" disabled={page >= totalPages} onClick={() => token && load(token, page + 1, { search, action: actionFilter, result: resultFilter, actor: actorFilter })}>
              Next <ChevronRight size={14} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default AuditLogScreen;
