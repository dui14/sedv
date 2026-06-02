"use client";

import { type ChangeEvent, type DragEvent, type FormEvent, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  CloudUpload,
  FileText,
  FolderLock,
  FolderOpen,
  Globe,
  Loader2,
  X,
} from "lucide-react";

import { ApiClientError, buildApiUrl } from "../../lib/api";
import type { FileItem } from "../../types";

import styles from "./upload-modal.module.css";

type Props = {
  token: string;
  userRole: "company" | "admin" | "manager" | "user";
  onClose: () => void;
  onUploaded: (file: FileItem) => void;
};

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

export function UploadModal({ token, userRole, onClose, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [vaultType, setVaultType] = useState<"floor" | "company" | "private">("floor");
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const busy = uploadStatus === "uploading";
  const isPrivileged = userRole !== "user";

  function pick(f: File | null | undefined) {
    if (!f) return;
    setFile(f);
    setError(null);
    setUploadStatus("idle");
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file || busy) return;
    setUploadStatus("uploading");
    setError(null);
    const form = new FormData();
    form.append("uploaded_file", file);
    form.append("vault_type", vaultType);
    try {
      const res = await fetch(buildApiUrl("/api/files"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const err = data?.error;
        throw new ApiClientError(err?.message ?? "Upload failed.", err?.code ?? "upload_failed", res.status);
      }
      setUploadStatus("done");
      onUploaded(data as FileItem);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setUploadStatus("error");
    }
  }

  return (
    <div className={styles.backdrop} role="presentation">
      <section className={styles.sheet} role="dialog" aria-modal="true" aria-label="Upload file">
        <header className={styles.header}>
          <h1 className={styles.title}>Upload file</h1>
          <button className={styles.closeBtn} type="button" aria-label="Close" disabled={busy} onClick={onClose}>
            <X size={18} />
          </button>
        </header>

        <form className={styles.body} onSubmit={handleSubmit} noValidate>
          <div
            className={`${styles.dropZone} ${dragActive ? styles.dropActive : ""} ${file ? styles.dropHasFile : ""}`}
            onDragEnter={() => setDragActive(true)}
            onDragLeave={() => setDragActive(false)}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDrop={(e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setDragActive(false); pick(e.dataTransfer.files?.[0]); }}
          >
            <input
              ref={inputRef}
              type="file"
              className={styles.hiddenInput}
              onChange={(e: ChangeEvent<HTMLInputElement>) => pick(e.currentTarget.files?.[0])}
            />
            <div className={styles.dropIcon}>
              {file ? <FileText size={22} /> : <CloudUpload size={22} />}
            </div>
            <p className={styles.dropTitle}>
              {file ? file.name : "Drop file here or choose"}
            </p>
            {file && <p className={styles.dropMeta}>{fmtBytes(file.size)}</p>}
            <button
              className={styles.secondaryButton}
              type="button"
              disabled={busy}
              onClick={() => inputRef.current?.click()}
            >
              <FolderOpen size={14} />
              {file ? "Change file" : "Choose file"}
            </button>
          </div>

          <div className={styles.vaultSelect}>
            <p className={styles.vaultLabel}>Destination vault</p>
            <div className={styles.vaultOptions}>
              <label className={`${styles.vaultOption} ${vaultType === "floor" ? styles.vaultOptionActive : ""}`}>
                <input
                  type="radio"
                  name="vault_type"
                  value="floor"
                  className={styles.hiddenInput}
                  checked={vaultType === "floor"}
                  onChange={() => setVaultType("floor")}
                />
                <Globe size={16} />
                <div>
                  <p className={styles.vaultOptionName}>Floor Vault</p>
                  <p className={styles.vaultOptionDesc}>
                    {isPrivileged ? "Visible to all floor members (auto-published)" : "Requires manager approval before visible"}
                  </p>
                </div>
              </label>

              {isPrivileged && (
                <label className={`${styles.vaultOption} ${vaultType === "company" ? styles.vaultOptionActive : ""}`}>
                  <input
                    type="radio"
                    name="vault_type"
                    value="company"
                    className={styles.hiddenInput}
                    checked={vaultType === "company"}
                    onChange={() => setVaultType("company")}
                  />
                  <Globe size={16} />
                  <div>
                    <p className={styles.vaultOptionName}>Company Vault</p>
                    <p className={styles.vaultOptionDesc}>Visible to all floors company-wide (auto-published)</p>
                  </div>
                </label>
              )}

              <label className={`${styles.vaultOption} ${vaultType === "private" ? styles.vaultOptionActive : ""}`}>
                <input
                  type="radio"
                  name="vault_type"
                  value="private"
                  className={styles.hiddenInput}
                  checked={vaultType === "private"}
                  onChange={() => setVaultType("private")}
                />
                <FolderLock size={16} />
                <div>
                  <p className={styles.vaultOptionName}>Private Vault</p>
                  <p className={styles.vaultOptionDesc}>Only visible to you — request publish to share</p>
                </div>
              </label>
            </div>
          </div>

          {uploadStatus === "error" && error && (
            <div className={styles.errorBanner} role="alert">
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          {uploadStatus === "done" && (
            <div className={styles.successBanner} role="status">
              <CheckCircle2 size={15} />
              <span>File uploaded and encrypted successfully.</span>
            </div>
          )}

          <footer className={styles.footer}>
            <button className={styles.secondaryButton} type="button" disabled={busy} onClick={onClose}>
              Cancel
            </button>
            <button className={styles.primaryButton} type="submit" disabled={busy || !file}>
              {busy ? <><Loader2 size={15} className={styles.spinner} /> Uploading…</> : <><CloudUpload size={15} /> Upload</>}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default UploadModal;
