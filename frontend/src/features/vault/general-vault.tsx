"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2, ChevronLeft, ChevronRight, CircleAlert, Download,
  FileText, Globe, Loader2, RefreshCw, Search, Upload,
} from "lucide-react";

import { apiRequest, authHeaders, buildApiUrl } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuthUser, FileItem, FileListResponse } from "../../types";
import { UploadModal } from "../files/upload-modal";

import styles from "./vault.module.css";

function fmtBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}
function fmtDate(s: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(s));
}

const STATUS_LABEL: Record<string, string> = { pending: "Pending", published: "Published", rejected: "Rejected" };
const STATUS_CLS: Record<string, string> = { pending: styles.tagPending, published: styles.tagPublished, rejected: styles.tagRejected };

export function GeneralVault() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const PAGE_SIZE = 15;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const t = getAccessToken();
    if (!t) { router.replace("/login"); return; }
    setToken(t);
    apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(t) })
      .then((u) => { setUser(u); return load(t, 1, ""); })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function load(t: string, p: number, s: string) {
    setLoading(true); setError(null);
    const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE), vault_type: "general" });
    if (s.trim()) params.set("search", s.trim());
    try {
      const data = await apiRequest<FileListResponse>(`/api/files?${params}`, { headers: authHeaders(t) });
      setFiles(data.items); setTotal(data.total); setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load files.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(file: FileItem) {
    if (!token) return;
    setActionLoading(file.file_id);
    try {
      const res = await fetch(buildApiUrl(`/api/files/${file.file_id}/download`), { headers: authHeaders(token) });
      if (!res.ok) { const p = await res.json().catch(() => null); throw new Error(p?.error?.message ?? "Download failed."); }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = file.original_name;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      setSuccess(`Downloaded ${file.original_name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    } finally {
      setActionLoading(null);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSubmitted(search.trim()); void load(token, 1, search.trim());
  }

  const canSeeAll = user?.role === "admin" || user?.role === "manager";

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.titleRow}>
          <Globe size={20} className={styles.titleIcon} />
          <div>
            <h1 className={styles.pageTitle}>General Vault</h1>
            <p className={styles.pageSubtitle}>
              {canSeeAll ? "All general vault files (any status)." : "Published files available to your organization."}
            </p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.secondaryButton} type="button" onClick={() => token && load(token, page, submitted)}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className={styles.primaryButton} type="button" onClick={() => setUploadOpen(true)}>
            <Upload size={14} /> Upload
          </button>
        </div>
      </div>

      {success && <div className={styles.successBanner} role="status"><CheckCircle2 size={15} /><span>{success}</span></div>}
      {error && <div className={styles.errorBanner} role="alert"><CircleAlert size={15} /><span>{error}</span></div>}

      <form className={styles.searchBar} onSubmit={handleSearch}>
        <div className={styles.searchInput}>
          <Search size={15} className={styles.searchIcon} />
          <input type="search" placeholder="Search files" value={search} onChange={(e) => setSearch(e.target.value)} className={styles.searchField} disabled={loading} />
        </div>
        <button className={styles.secondaryButton} type="submit" disabled={loading}>Search</button>
      </form>

      {loading && <div className={styles.loading}><Loader2 size={20} className={styles.spinner} /><span>Loading…</span></div>}
      {!loading && files.length === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}><FileText size={24} /></div>
          <p className={styles.emptyTitle}>{submitted ? "No matching files" : "No files yet"}</p>
          <p className={styles.emptyText}>{submitted ? "Try a different search term." : "Upload a file to the general vault."}</p>
        </div>
      )}

      {!loading && files.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Owner</th>
                  <th>Size</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => {
                  const busy = actionLoading === f.file_id;
                  const canDownload = f.publish_status === "published" || canSeeAll || f.owner_user_id === user?.user_id;
                  return (
                    <tr key={f.file_id}>
                      <td className={styles.tdFile}><FileText size={14} className={styles.fileIcon} /><span>{f.original_name}</span></td>
                      <td><span className={STATUS_CLS[f.publish_status] ?? styles.tagNa}>{STATUS_LABEL[f.publish_status] ?? f.publish_status}</span></td>
                      <td className={styles.tdMuted}>{f.owner_name}</td>
                      <td className={styles.tdMuted}>{fmtBytes(f.size_bytes)}</td>
                      <td className={styles.tdMuted}>{fmtDate(f.created_at)}</td>
                      <td>
                        {canDownload && (
                          <button className={styles.iconBtn} type="button" title="Download" disabled={busy} onClick={() => handleDownload(f)}>
                            {busy ? <Loader2 size={14} className={styles.spinner} /> : <Download size={14} />}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.secondaryButton} type="button" disabled={page <= 1} onClick={() => token && load(token, page - 1, submitted)}>
                <ChevronLeft size={14} /> Previous
              </button>
              <span className={styles.pageInfo}>Page {page} of {totalPages}</span>
              <button className={styles.secondaryButton} type="button" disabled={page >= totalPages} onClick={() => token && load(token, page + 1, submitted)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}

      {uploadOpen && token && (
        <UploadModal
          token={token}
          userRole={user?.role ?? "user"}
          onClose={() => setUploadOpen(false)}
          onUploaded={(f) => { setUploadOpen(false); setSuccess(`Uploaded ${f.original_name}.`); if (token) void load(token, 1, submitted); }}
        />
      )}
    </div>
  );
}
