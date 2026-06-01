"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Download,
  FileText,
  Info,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  X,
} from "lucide-react";

import { apiRequest, authHeaders, buildApiUrl } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuthUser, FileDeleteResponse, FileItem, FileListResponse } from "../../types";
import { UploadModal } from "./upload-modal";

import styles from "./vault-dashboard.module.css";

type ViewState = "loading" | "error" | "empty" | "default";

function fmtBytes(n: number): string {
	if (n < 1024) return `${n} B`;
	if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
	return `${(n / 1048576).toFixed(1)} MB`;
}

function fmtDate(s: string): string {
	return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(s));
}

const STATUS_COLORS: Record<string, string> = {
	pending: styles.tagPending,
	published: styles.tagPublished,
	rejected: styles.tagRejected,
	na: styles.tagNa,
	active: styles.tagPublished,
};

const STATUS_LABELS: Record<string, string> = {
	pending: "Pending",
	published: "Published",
	rejected: "Rejected",
	na: "Private",
	active: "Active",
};

export function VaultDashboard() {
	const router = useRouter();
	const [user, setUser] = useState<AuthUser | null>(null);
	const [token, setToken] = useState<string | null>(null);
	const [files, setFiles] = useState<FileItem[]>([]);
	const [total, setTotal] = useState(0);
	const [page, setPage] = useState(1);
	const [search, setSearch] = useState("");
	const [submitted, setSubmitted] = useState("");
	const [viewState, setViewState] = useState<ViewState>("loading");
	const [errorMsg, setErrorMsg] = useState<string | null>(null);
	const [successMsg, setSuccessMsg] = useState<string | null>(null);
	const [isUploadOpen, setIsUploadOpen] = useState(false);
	const [detailFile, setDetailFile] = useState<FileItem | null>(null);
	const [actionLoading, setActionLoading] = useState<string | null>(null);
	const PAGE_SIZE = 15;
	const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

	useEffect(() => {
		const t = getAccessToken();
		if (!t) { router.replace("/login"); return; }
		setToken(t);
		apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(t) })
			.then((u) => { setUser(u); return loadFiles(t, 1, ""); })
			.catch(() => router.replace("/login"));
	}, [router]);

	async function loadFiles(t: string, p: number, s: string) {
		setViewState("loading");
		setErrorMsg(null);
		const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE) });
		if (s.trim()) params.set("search", s.trim());
		try {
			const data = await apiRequest<FileListResponse>(`/api/files?${params}`, { headers: authHeaders(t) });
			setFiles(data.items);
			setTotal(data.total);
			setPage(data.page);
			setViewState(data.items.length === 0 ? "empty" : "default");
		} catch (err) {
			setErrorMsg(err instanceof Error ? err.message : "Could not load files.");
			setViewState("error");
		}
	}

	function handleSearch(e: FormEvent<HTMLFormElement>) {
		e.preventDefault();
		if (!token) return;
		setSubmitted(search.trim());
		void loadFiles(token, 1, search.trim());
	}

	async function handleDownload(file: FileItem) {
		if (!token) return;
		setActionLoading(file.file_id);
		setSuccessMsg(null);
		try {
			const res = await fetch(buildApiUrl(`/api/files/${file.file_id}/download`), { headers: authHeaders(token) });
			if (!res.ok) {
				const p = await res.json().catch(() => null);
				throw new Error(p?.error?.message ?? "Download failed.");
			}
			const blob = await res.blob();
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url; a.download = file.original_name;
			document.body.appendChild(a); a.click(); a.remove();
			URL.revokeObjectURL(url);
			setSuccessMsg(`Downloaded ${file.original_name}.`);
		} catch (err) {
			setErrorMsg(err instanceof Error ? err.message : "Download failed.");
		} finally {
			setActionLoading(null);
		}
	}

	async function handleDelete(file: FileItem) {
		if (!token || !window.confirm(`Delete "${file.original_name}"?`)) return;
		setActionLoading(file.file_id);
		try {
			await apiRequest<FileDeleteResponse>(`/api/files/${file.file_id}`, { method: "DELETE", headers: authHeaders(token) });
			setSuccessMsg(`Deleted ${file.original_name}.`);
			await loadFiles(token, page, submitted);
		} catch (err) {
			setErrorMsg(err instanceof Error ? err.message : "Delete failed.");
		} finally {
			setActionLoading(null);
		}
	}

	async function handleRequestPublish(file: FileItem) {
		if (!token) return;
		setActionLoading(file.file_id);
		try {
			await apiRequest(`/api/files/${file.file_id}/request-publish`, { method: "POST", headers: authHeaders(token) });
			setSuccessMsg(`Publish request submitted for ${file.original_name}.`);
			await loadFiles(token, page, submitted);
		} catch (err) {
			setErrorMsg(err instanceof Error ? err.message : "Request failed.");
		} finally {
			setActionLoading(null);
		}
	}

	const canDelete = (file: FileItem) =>
		user?.role === "admin" || user?.role === "manager" || file.owner_user_id === user?.user_id;

	const canRequestPublish = (file: FileItem) =>
		user?.role === "user" && file.vault_type === "private" && file.owner_user_id === user?.user_id;

	return (
		<div className={styles.page}>
			<div className={styles.pageHeader}>
				<div>
					<h1 className={styles.pageTitle}>Vault</h1>
					<p className={styles.pageSubtitle}>General and private files visible to your role.</p>
				</div>
				<div className={styles.headerActions}>
					{token && (
						<button
							className={styles.secondaryButton}
							type="button"
							onClick={() => token && loadFiles(token, page, submitted)}
						>
							<RefreshCw size={15} />
							Refresh
						</button>
					)}
					<button
						className={styles.primaryButton}
						type="button"
						onClick={() => setIsUploadOpen(true)}
					>
						<Upload size={15} />
						Upload
					</button>
				</div>
			</div>

			{successMsg && (
				<div className={styles.successBanner} role="status">
					<CheckCircle2 size={16} />
					<span>{successMsg}</span>
				</div>
			)}
			{errorMsg && (
				<div className={styles.errorBanner} role="alert">
					<CircleAlert size={16} />
					<span>{errorMsg}</span>
				</div>
			)}

			<form className={styles.searchBar} onSubmit={handleSearch}>
				<div className={styles.searchInput}>
					<Search size={15} className={styles.searchIcon} />
					<input
						type="search"
						placeholder="Search by name or type"
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						className={styles.searchField}
						disabled={viewState === "loading"}
					/>
				</div>
				<button className={styles.secondaryButton} type="submit" disabled={viewState === "loading"}>
					Search
				</button>
			</form>

			{viewState === "loading" && (
				<div className={styles.loadingState}>
					<Loader2 size={22} className={styles.spinner} />
					<span>Loading files…</span>
				</div>
			)}

			{viewState === "error" && (
				<div className={styles.errorState} role="alert">
					<CircleAlert size={20} />
					<div>
						<p className={styles.errorStateTitle}>Could not load files</p>
						<p className={styles.errorStateText}>{errorMsg}</p>
					</div>
					<button className={styles.secondaryButton} type="button" onClick={() => token && loadFiles(token, page, submitted)}>
						Retry
					</button>
				</div>
			)}

			{viewState === "empty" && (
				<div className={styles.emptyState}>
					<div className={styles.emptyIcon}><FileText size={24} /></div>
					<p className={styles.emptyTitle}>No files found</p>
					<p className={styles.emptyText}>
						{submitted ? "No files match your search." : "Upload a file to get started."}
					</p>
					{submitted && (
						<button className={styles.secondaryButton} type="button" onClick={() => { setSearch(""); setSubmitted(""); token && loadFiles(token, 1, ""); }}>
							Clear search
						</button>
					)}
				</div>
			)}

			{viewState === "default" && (
				<>
					<div className={styles.tableWrap}>
						<table className={styles.table}>
							<thead>
								<tr>
									<th>Name</th>
									<th>Vault</th>
									<th>Status</th>
									<th>Owner</th>
									<th>Size</th>
									<th>Date</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{files.map((file) => {
									const busy = actionLoading === file.file_id;
									return (
										<tr key={file.file_id}>
											<td className={styles.tdName}>
												<FileText size={14} className={styles.fileIcon} />
												<span>{file.original_name}</span>
											</td>
											<td>
												<span className={file.vault_type === "private" ? styles.tagPrivate : styles.tagGeneral}>
													{file.vault_type === "private" ? "Private" : "General"}
												</span>
											</td>
											<td>
												<span className={STATUS_COLORS[file.publish_status] ?? styles.tagNa}>
													{STATUS_LABELS[file.publish_status] ?? file.publish_status}
												</span>
											</td>
											<td className={styles.tdMuted}>{file.owner_name}</td>
											<td className={styles.tdMuted}>{fmtBytes(file.size_bytes)}</td>
											<td className={styles.tdMuted}>{fmtDate(file.created_at)}</td>
											<td>
												<div className={styles.actions}>
													<button
														className={styles.actionBtn}
														type="button"
														title="File details"
														onClick={() => setDetailFile(file)}
													>
														<Info size={14} />
													</button>
													<button
														className={styles.actionBtn}
														type="button"
														title="Download"
														disabled={busy}
														onClick={() => handleDownload(file)}
													>
														{busy ? <Loader2 size={14} className={styles.spinner} /> : <Download size={14} />}
													</button>
													{canRequestPublish(file) && (
														<button
															className={styles.actionBtn}
															type="button"
															title="Request publish"
															disabled={busy}
															onClick={() => handleRequestPublish(file)}
														>
															<Upload size={14} />
														</button>
													)}
													{canDelete(file) && (
														<button
															className={`${styles.actionBtn} ${styles.actionBtnDanger}`}
															type="button"
															title="Delete"
															disabled={busy}
															onClick={() => handleDelete(file)}
														>
															<Trash2 size={14} />
														</button>
													)}
												</div>
											</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>

					<div className={styles.mobileList}>
						{files.map((file) => {
							const busy = actionLoading === file.file_id;
							return (
								<div key={file.file_id} className={styles.mobileCard}>
									<div className={styles.mobileCardHeader}>
										<FileText size={16} className={styles.fileIcon} />
										<span className={styles.mobileCardName}>{file.original_name}</span>
										<span className={STATUS_COLORS[file.publish_status] ?? styles.tagNa}>
											{STATUS_LABELS[file.publish_status] ?? file.publish_status}
										</span>
									</div>
									<div className={styles.mobileCardMeta}>
										<span>{file.owner_name}</span>
										<span>{fmtBytes(file.size_bytes)}</span>
										<span>{fmtDate(file.created_at)}</span>
									</div>
									<div className={styles.actions}>
										<button className={styles.actionBtn} type="button" title="File details" onClick={() => setDetailFile(file)}>
											<Info size={14} />
										</button>
										<button className={styles.actionBtn} type="button" title="Download" disabled={busy} onClick={() => handleDownload(file)}>
											{busy ? <Loader2 size={14} className={styles.spinner} /> : <Download size={14} />}
										</button>
										{canRequestPublish(file) && (
											<button className={styles.actionBtn} type="button" title="Request publish" disabled={busy} onClick={() => handleRequestPublish(file)}>
												<Upload size={14} />
											</button>
										)}
										{canDelete(file) && (
											<button className={`${styles.actionBtn} ${styles.actionBtnDanger}`} type="button" title="Delete" disabled={busy} onClick={() => handleDelete(file)}>
												<Trash2 size={14} />
											</button>
										)}
									</div>
								</div>
							);
						})}
					</div>

					{totalPages > 1 && (
						<div className={styles.pagination}>
							<button
								className={styles.secondaryButton}
								type="button"
								disabled={page <= 1}
								onClick={() => token && loadFiles(token, page - 1, submitted)}
							>
								<ChevronLeft size={15} /> Previous
							</button>
							<span className={styles.pageInfo}>Page {page} of {totalPages}</span>
							<button
								className={styles.secondaryButton}
								type="button"
								disabled={page >= totalPages}
								onClick={() => token && loadFiles(token, page + 1, submitted)}
							>
								Next <ChevronRight size={15} />
							</button>
						</div>
					)}
				</>
			)}

			{isUploadOpen && token && (
				<UploadModal
					token={token}
					userRole={user?.role ?? "user"}
					onClose={() => setIsUploadOpen(false)}
					onUploaded={(file) => {
						setIsUploadOpen(false);
						setSuccessMsg(`Uploaded ${file.original_name}.`);
						if (token) void loadFiles(token, 1, submitted);
					}}
				/>
			)}

			{detailFile && (
				<div className={styles.modalBackdrop} role="presentation" onClick={() => setDetailFile(null)}>
					<section
						className={styles.detailModal}
						role="dialog"
						aria-modal="true"
						aria-label={`File details for ${detailFile.original_name}`}
						onClick={(event) => event.stopPropagation()}
					>
						<div className={styles.detailHeader}>
							<div>
								<h2 className={styles.detailTitle}>{detailFile.original_name}</h2>
								<p className={styles.detailSubtitle}>Review metadata before downloading.</p>
							</div>
							<button className={styles.actionBtn} type="button" title="Close details" onClick={() => setDetailFile(null)}>
								<X size={14} />
							</button>
						</div>

						<div className={styles.detailStatusRow}>
							<span className={detailFile.vault_type === "private" ? styles.tagPrivate : styles.tagGeneral}>
								{detailFile.vault_type === "private" ? "Private" : "General"}
							</span>
							<span className={STATUS_COLORS[detailFile.publish_status] ?? styles.tagNa}>
								{STATUS_LABELS[detailFile.publish_status] ?? detailFile.publish_status}
							</span>
						</div>

						<dl className={styles.detailGrid}>
							<div><dt>Owner</dt><dd>{detailFile.owner_name || "Unknown"}</dd></div>
							<div><dt>MIME type</dt><dd>{detailFile.mime_type}</dd></div>
							<div><dt>Size</dt><dd>{fmtBytes(detailFile.size_bytes)}</dd></div>
							<div><dt>Uploaded</dt><dd>{fmtDate(detailFile.created_at)}</dd></div>
							<div><dt>Updated</dt><dd>{fmtDate(detailFile.updated_at)}</dd></div>
							<div><dt>Encryption</dt><dd>{detailFile.encryption_algorithm}</dd></div>
							<div className={styles.detailWide}><dt>SHA-256</dt><dd className={styles.hashValue}>{detailFile.sha256}</dd></div>
							{detailFile.reviewed_at && <div><dt>Reviewed</dt><dd>{fmtDate(detailFile.reviewed_at)}</dd></div>}
							{detailFile.review_note && <div className={styles.detailWide}><dt>Review note</dt><dd>{detailFile.review_note}</dd></div>}
						</dl>

						<div className={styles.detailActions}>
							<button className={styles.secondaryButton} type="button" onClick={() => setDetailFile(null)}>
								Close
							</button>
							<button className={styles.primaryButton} type="button" onClick={() => handleDownload(detailFile)} disabled={actionLoading === detailFile.file_id}>
								{actionLoading === detailFile.file_id ? <><Loader2 size={15} className={styles.spinner} /> Downloading...</> : <><Download size={15} /> Download file</>}
							</button>
						</div>
					</section>
				</div>
			)}
		</div>
	);
}

export default VaultDashboard;
