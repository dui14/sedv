"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  FileText,
  Loader2,
  RefreshCw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

import { apiRequest, authHeaders, buildApiUrl } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuthUser, FileItem, FileListResponse } from "../../types";

import styles from "./approval-queue.module.css";

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

function fmtDate(s: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(s));
}

export function ApprovalQueue() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [noteModal, setNoteModal] = useState<{ fileId: string; action: "approve" | "reject" } | null>(null);
  const [noteText, setNoteText] = useState("");
  const PAGE_SIZE = 15;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const t = getAccessToken();
    if (!t) { router.replace("/login"); return; }
    setToken(t);
    apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(t) })
      .then((u) => {
        setUser(u);
        if (!["admin", "manager"].includes(u.role)) { router.replace("/dashboard"); return; }
        return load(t, 1);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function load(t: string, p: number) {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE) });
      const data = await apiRequest<FileListResponse>(`/api/files/approvals?${params}`, { headers: authHeaders(t) });
      setFiles(data.items); setTotal(data.total); setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load queue.");
    } finally {
      setLoading(false);
    }
  }

  function openNote(fileId: string, action: "approve" | "reject") {
    setNoteText(""); setNoteModal({ fileId, action });
  }

  async function submitAction() {
    if (!noteModal || !token) return;
    const { fileId, action } = noteModal;
    setActionLoading(fileId); setNoteModal(null);
    setSuccess(null); setError(null);
    try {
      const endpoint = `/api/files/${fileId}/${action}`;
      await apiRequest(endpoint, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({ note: noteText.trim() || null }),
      });
      setSuccess(`File ${action === "approve" ? "approved" : "rejected"}.`);
      await load(token, page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Approval Queue</h1>
          <p className={styles.pageSubtitle}>Review pending general vault files.</p>
        </div>
        <button className={styles.secondaryButton} type="button" onClick={() => token && load(token, page)}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {success && (
        <div className={styles.successBanner} role="status">
          <CheckCircle2 size={15} /><span>{success}</span>
        </div>
      )}
      {error && (
        <div className={styles.errorBanner} role="alert">
          <CircleAlert size={15} /><span>{error}</span>
        </div>
      )}

      {loading && (
        <div className={styles.loading}>
          <Loader2 size={20} className={styles.spinner} /><span>Loading queue…</span>
        </div>
      )}

      {!loading && files.length === 0 && (
        <div className={styles.empty}>
          <CheckCircle2 size={32} className={styles.emptyIcon} />
          <p className={styles.emptyTitle}>Queue is clear</p>
          <p className={styles.emptyText}>No files are pending approval.</p>
        </div>
      )}

      {!loading && files.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Owner</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => {
                  const busy = actionLoading === f.file_id;
                  return (
                    <tr key={f.file_id}>
                      <td className={styles.tdFile}>
                        <FileText size={14} className={styles.fileIcon} />
                        <span>{f.original_name}</span>
                      </td>
                      <td className={styles.tdMuted}>{f.owner_name}</td>
                      <td className={styles.tdMuted}>{fmtBytes(f.size_bytes)}</td>
                      <td className={styles.tdMuted}>{fmtDate(f.created_at)}</td>
                      <td>
                        <div className={styles.actions}>
                          <button
                            className={`${styles.actionBtn} ${styles.approveBtn}`}
                            type="button"
                            title="Approve"
                            disabled={busy}
                            onClick={() => openNote(f.file_id, "approve")}
                          >
                            {busy ? <Loader2 size={14} className={styles.spinner} /> : <ThumbsUp size={14} />}
                            Approve
                          </button>
                          <button
                            className={`${styles.actionBtn} ${styles.rejectBtn}`}
                            type="button"
                            title="Reject"
                            disabled={busy}
                            onClick={() => openNote(f.file_id, "reject")}
                          >
                            <ThumbsDown size={14} /> Reject
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

      {noteModal && (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>
            <h2 className={styles.modalTitle}>
              {noteModal.action === "approve" ? "Approve file" : "Reject file"}
            </h2>
            <p className={styles.modalText}>Add an optional note for this decision.</p>
            <textarea
              className={styles.noteInput}
              placeholder="Optional note…"
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              rows={3}
            />
            <div className={styles.modalActions}>
              <button className={styles.secondaryButton} type="button" onClick={() => setNoteModal(null)}>Cancel</button>
              <button
                className={noteModal.action === "approve" ? styles.approveButton : styles.rejectButton}
                type="button"
                onClick={submitAction}
              >
                {noteModal.action === "approve" ? <ThumbsUp size={14} /> : <ThumbsDown size={14} />}
                {noteModal.action === "approve" ? "Confirm approve" : "Confirm reject"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ApprovalQueue;
