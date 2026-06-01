"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronLeft, ChevronRight, CircleAlert, Download, FileText, FolderLock,
  Loader2, RefreshCw, Trash2, Upload,
} from "lucide-react";

import { apiRequest, authHeaders, buildApiUrl } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuthUser, FileDeleteResponse, FileItem, FileListResponse } from "../../types";
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

export function PrivateVault() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
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
      .then((u) => {
        setUser(u);
        if (u.role !== "user") { router.replace("/dashboard"); return; }
        return load(t, 1);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function load(t: string, p: number) {
    setLoading(true); setError(null);
    const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE), vault_type: "private" });
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

  async function handleDelete(file: FileItem) {
    if (!token || !window.confirm(`Delete "${file.original_name}"?`)) return;
    setActionLoading(file.file_id);
    try {
      await apiRequest<FileDeleteResponse>(`/api/files/${file.file_id}`, { method: "DELETE", headers: authHeaders(token) });
      setSuccess(`Deleted ${file.original_name}.`);
      if (token) await load(token, page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleRequestPublish(file: FileItem) {
    if (!token) return;
    setActionLoading(file.file_id);
    try {
      await apiRequest(`/api/files/${file.file_id}/request-publish`, { method: "POST", headers: authHeaders(token) });
      setSuccess(`Publish request submitted for ${file.original_name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.titleRow}>
          <FolderLock size={20} className={styles.titleIconPrivate} />
          <div>
            <h1 className={styles.pageTitle}>Private Vault</h1>
            <p className={styles.pageSubtitle}>Only you can see these files. Request publish to share with the company.</p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.secondaryButton} type="button" onClick={() => token && load(token, page)}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className={styles.primaryButton} type="button" onClick={() => setUploadOpen(true)}>
            <Upload size={14} /> Upload
          </button>
        </div>
      </div>

      {success && <div className={styles.successBanner} role="status">{success}</div>}
      {error && <div className={styles.errorBanner} role="alert"><CircleAlert size={15} /><span>{error}</span></div>}

      {loading && <div className={styles.loading}><Loader2 size={20} className={styles.spinner} /><span>Loading…</span></div>}
      {!loading && files.length === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}><FolderLock size={24} /></div>
          <p className={styles.emptyTitle}>No private files</p>
          <p className={styles.emptyText}>Upload files here to keep them private.</p>
        </div>
      )}

      {!loading && files.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>Name</th><th>Size</th><th>Uploaded</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {files.map((f) => {
                  const busy = actionLoading === f.file_id;
                  return (
                    <tr key={f.file_id}>
                      <td className={styles.tdFile}><FileText size={14} className={styles.fileIcon} /><span>{f.original_name}</span></td>
                      <td className={styles.tdMuted}>{fmtBytes(f.size_bytes)}</td>
                      <td className={styles.tdMuted}>{fmtDate(f.created_at)}</td>
                      <td>
                        <div className={styles.actions}>
                          <button className={styles.iconBtn} type="button" title="Download" disabled={busy} onClick={() => handleDownload(f)}>
                            {busy ? <Loader2 size={14} className={styles.spinner} /> : <Download size={14} />}
                          </button>
                          <button className={`${styles.iconBtn} ${styles.publishBtn}`} type="button" title="Request publish" disabled={busy} onClick={() => handleRequestPublish(f)}>
                            <Upload size={14} />
                          </button>
                          <button className={`${styles.iconBtn} ${styles.deleteBtn}`} type="button" title="Delete" disabled={busy} onClick={() => handleDelete(f)}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
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

      {uploadOpen && token && (
        <UploadModal
          token={token}
          userRole="user"
          onClose={() => setUploadOpen(false)}
          onUploaded={(f) => { setUploadOpen(false); setSuccess(`Uploaded ${f.original_name}.`); if (token) void load(token, 1); }}
        />
      )}
    </div>
  );
}
