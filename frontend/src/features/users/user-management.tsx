"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight, Building2, CheckCircle2, ChevronLeft, ChevronRight, CircleAlert,
  Loader2, Pencil, RefreshCw, Search, ThumbsDown, ThumbsUp, Trash2, UserPlus, Users,
} from "lucide-react";

import { apiRequest, authHeaders } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import type { AuthUser, FloorItem, FloorListResponse, UserItem, UserListResponse } from "../../types";

import styles from "./user-management.module.css";

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(s));
}

const ROLE_LABEL: Record<string, string> = { company: "Company", admin: "Admin", manager: "Manager", user: "User" };
const ROLE_CLS: Record<string, string> = { company: styles.roleCompany, admin: styles.roleAdmin, manager: styles.roleManager, user: styles.roleUser };
const STATUS_CLS: Record<string, string> = { active: styles.statusActive, disabled: styles.statusDisabled, pending: styles.statusPending };

type FormRole = "company" | "admin" | "manager" | "user";
type FormStatus = "active" | "disabled" | "pending";
type UserModal = { mode: "create" } | { mode: "edit"; user: UserItem } | null;

export function UserManagement() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<AuthUser | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [transfers, setTransfers] = useState<UserItem[]>([]);
  const [floors, setFloors] = useState<FloorItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [modal, setModal] = useState<UserModal>(null);
  const [formState, setFormState] = useState({
    email: "", full_name: "", password: "", role: "user" as FormRole,
    status: "active" as FormStatus, floor_id: "" as string,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const PAGE_SIZE = 15;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const t = getAccessToken();
    if (!t) { router.replace("/login"); return; }
    setToken(t);
    apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(t) })
      .then((u) => {
        setMe(u);
        if (u.role !== "admin" && u.role !== "company") { router.replace("/dashboard"); return; }
        return Promise.all([load(t, 1, ""), loadFloors(t), loadTransfers(t)]);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  const isCompany = me?.role === "company";

  async function load(t: string, p: number, s: string) {
    setLoading(true); setError(null);
    const params = new URLSearchParams({ page: String(p), page_size: String(PAGE_SIZE) });
    if (s.trim()) params.set("search", s.trim());
    try {
      const data = await apiRequest<UserListResponse>(`/api/users?${params}`, { headers: authHeaders(t) });
      setUsers(data.items); setTotal(data.total); setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load users.");
    } finally {
      setLoading(false);
    }
  }

  async function loadFloors(t: string) {
    try {
      const data = await apiRequest<FloorListResponse>("/api/floors", { headers: authHeaders(t) });
      setFloors(data.items);
    } catch {
      // non-fatal
    }
  }

  async function loadTransfers(t: string) {
    try {
      const data = await apiRequest<UserListResponse>("/api/users/transfer-requests", { headers: authHeaders(t) });
      setTransfers(data.items);
    } catch {
      // non-fatal
    }
  }

  function openCreate() {
    setFormState({ email: "", full_name: "", password: "", role: "user", status: "active", floor_id: isCompany ? "" : (me?.floor_id ?? "") });
    setFormError(null); setModal({ mode: "create" });
  }

  function openEdit(user: UserItem) {
    if (!isCompany && user.role === "admin") return;
    if (!isCompany && user.role === "company") return;
    setFormState({ email: user.email, full_name: user.full_name, password: "", role: user.role, status: user.status, floor_id: user.floor_id ?? "" });
    setFormError(null); setModal({ mode: "edit", user });
  }

  async function handleSave() {
    if (!token || !modal) return;
    setFormLoading(true); setFormError(null);
    try {
      if (modal.mode === "create") {
        if (!formState.email || !formState.full_name || !formState.password) {
          setFormError("Email, name, and password are required."); return;
        }
        const body: Record<string, string | null> = {
          email: formState.email, full_name: formState.full_name,
          password: formState.password, role: formState.role,
        };
        if (isCompany && formState.floor_id) body.floor_id = formState.floor_id;
        await apiRequest("/api/users", {
          method: "POST",
          headers: { ...authHeaders(token), "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        setSuccess("User created.");
      } else {
        const patch: Record<string, string | null> = {};
        if (formState.email !== modal.user.email) patch.email = formState.email;
        if (formState.full_name !== modal.user.full_name) patch.full_name = formState.full_name;
        if (formState.role !== modal.user.role) patch.role = formState.role;
        if (formState.status !== modal.user.status) patch.status = formState.status;
        if (formState.password.trim()) patch.password = formState.password;
        if (formState.floor_id && formState.floor_id !== (modal.user.floor_id ?? "")) {
          patch.floor_id = formState.floor_id;
        }
        if (Object.keys(patch).length > 0) {
          await apiRequest(`/api/users/${modal.user.user_id}`, {
            method: "PATCH",
            headers: { ...authHeaders(token), "Content-Type": "application/json" },
            body: JSON.stringify(patch),
          });
        }
        setSuccess("User updated.");
      }
      setModal(null);
      await Promise.all([load(token, page, submitted), loadTransfers(token)]);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDelete(user: UserItem) {
    if (!token || !window.confirm(`Delete user "${user.full_name}"? This cannot be undone.`)) return;
    try {
      await apiRequest(`/api/users/${user.user_id}`, { method: "DELETE", headers: authHeaders(token) });
      setSuccess(`Deleted ${user.full_name}.`);
      if (token) await load(token, page, submitted);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  }

  async function handleTransfer(userId: string, action: "approve" | "reject") {
    if (!token) return;
    setActionLoading(userId);
    try {
      await apiRequest(`/api/users/${userId}/${action}-transfer`, {
        method: "POST", headers: authHeaders(token),
      });
      setSuccess(`Transfer ${action === "approve" ? "approved" : "rejected"}.`);
      await Promise.all([load(token, page, submitted), loadTransfers(token)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${action} failed.`);
    } finally {
      setActionLoading(null);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSubmitted(search.trim()); void load(token, 1, search.trim());
  }

  function canEdit(u: UserItem) {
    if (u.user_id === me?.user_id) return false;
    if (isCompany) return u.role !== "company";
    return u.role !== "admin" && u.role !== "company";
  }

  const availableRoles: FormRole[] = isCompany
    ? ["company", "admin", "manager", "user"]
    : ["manager", "user"];

  const floorOptions = floors.filter(f => isCompany || f.floor_id !== me?.floor_id || true);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.titleRow}>
          <Users size={20} className={styles.titleIcon} />
          <div>
            <h1 className={styles.pageTitle}>Users</h1>
            <p className={styles.pageSubtitle}>
              {isCompany ? "All organization accounts." : "Accounts within your floor."}
            </p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.secondaryButton} type="button" onClick={() => token && Promise.all([load(token, page, submitted), loadTransfers(token)])}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className={styles.primaryButton} type="button" onClick={openCreate}>
            <UserPlus size={14} /> Add user
          </button>
        </div>
      </div>

      {transfers.length > 0 && (
        <div className={styles.transferSection}>
          <h2 className={styles.transferTitle}>
            <ArrowRight size={15} /> Pending Floor Transfers ({transfers.length})
          </h2>
          <div className={styles.transferList}>
            {transfers.map((u) => {
              const busy = actionLoading === u.user_id;
              return (
                <div key={u.user_id} className={styles.transferCard}>
                  <div className={styles.transferInfo}>
                    <span className={styles.transferName}>{u.full_name}</span>
                    <span className={styles.transferEmail}>{u.email}</span>
                    <span className={styles.transferArrow}>
                      <Building2 size={12} /> {u.floor_name ?? u.floor_id ?? "—"}
                      <ArrowRight size={12} />
                      <Building2 size={12} /> {u.pending_floor_name ?? u.pending_floor_id ?? "—"}
                    </span>
                  </div>
                  <div className={styles.transferActions}>
                    <button
                      className={`${styles.actionBtn} ${styles.approveBtn}`}
                      type="button" disabled={busy}
                      onClick={() => handleTransfer(u.user_id, "approve")}
                    >
                      {busy ? <Loader2 size={13} className={styles.spinner} /> : <ThumbsUp size={13} />}
                      Approve
                    </button>
                    <button
                      className={`${styles.actionBtn} ${styles.rejectBtn}`}
                      type="button" disabled={busy}
                      onClick={() => handleTransfer(u.user_id, "reject")}
                    >
                      <ThumbsDown size={13} /> Reject
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {success && <div className={styles.successBanner} role="status"><CheckCircle2 size={15} /><span>{success}</span></div>}
      {error && <div className={styles.errorBanner} role="alert"><CircleAlert size={15} /><span>{error}</span></div>}

      <form className={styles.searchBar} onSubmit={handleSearch}>
        <div className={styles.searchWrap}>
          <Search size={15} className={styles.searchIcon} />
          <input type="search" placeholder="Search by name or email" value={search} onChange={(e) => setSearch(e.target.value)} className={styles.searchField} disabled={loading} />
        </div>
        <button className={styles.secondaryButton} type="submit" disabled={loading}>Search</button>
      </form>

      {loading && <div className={styles.loading}><Loader2 size={20} className={styles.spinner} /><span>Loading users…</span></div>}

      {!loading && users.length > 0 && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Floor</th>
                  <th>Status</th>
                  <th>Last login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.user_id} className={u.status === "pending" ? styles.rowPending : ""}>
                    <td className={styles.tdName}>{u.full_name}</td>
                    <td className={styles.tdMuted}>{u.email}</td>
                    <td><span className={ROLE_CLS[u.role] ?? styles.roleUser}>{ROLE_LABEL[u.role] ?? u.role}</span></td>
                    <td className={styles.tdMuted}>
                      {u.floor_name ? (
                        <span className={styles.floorTag}><Building2 size={11} />{u.floor_name}</span>
                      ) : "—"}
                      {u.pending_floor_name && (
                        <span className={styles.pendingFloorTag}>
                          <ArrowRight size={10} />{u.pending_floor_name}
                        </span>
                      )}
                    </td>
                    <td><span className={STATUS_CLS[u.status] ?? styles.statusPending}>{u.status}</span></td>
                    <td className={styles.tdMuted}>{fmtDate(u.last_login_at)}</td>
                    <td>
                      {canEdit(u) ? (
                        <div className={styles.actions}>
                          <button className={styles.iconBtn} type="button" title="Edit" onClick={() => openEdit(u)}>
                            <Pencil size={14} />
                          </button>
                          <button className={`${styles.iconBtn} ${styles.deleteBtn}`} type="button" title="Delete" onClick={() => handleDelete(u)}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ) : (
                        <span className={styles.tdMuted}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.secondaryButton} type="button" disabled={page <= 1} onClick={() => token && load(token, page - 1, submitted)}>
                <ChevronLeft size={14} /> Previous
              </button>
              <span className={styles.pageInfo}>Page {page} of {totalPages} ({total} total)</span>
              <button className={styles.secondaryButton} type="button" disabled={page >= totalPages} onClick={() => token && load(token, page + 1, submitted)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}

      {!loading && users.length === 0 && (
        <div className={styles.empty}>
          <p className={styles.emptyTitle}>{submitted ? "No users found" : "No users"}</p>
        </div>
      )}

      {modal && (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>
            <h2 className={styles.modalTitle}>{modal.mode === "create" ? "Add user" : "Edit user"}</h2>
            {formError && <div className={styles.formError}><CircleAlert size={14} /><span>{formError}</span></div>}
            <div className={styles.formGrid}>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>Full name</span>
                <input className={styles.input} type="text" value={formState.full_name} onChange={(e) => setFormState((s) => ({ ...s, full_name: e.target.value }))} disabled={formLoading} />
              </label>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>Email</span>
                <input className={styles.input} type="email" value={formState.email} onChange={(e) => setFormState((s) => ({ ...s, email: e.target.value }))} disabled={formLoading} />
              </label>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>{modal.mode === "create" ? "Password" : "New password"}</span>
                <input className={styles.input} type="password" placeholder={modal.mode === "edit" ? "Leave blank to keep current" : ""} value={formState.password} onChange={(e) => setFormState((s) => ({ ...s, password: e.target.value }))} disabled={formLoading} />
              </label>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>Role</span>
                <select className={styles.select} value={formState.role} onChange={(e) => setFormState((s) => ({ ...s, role: e.target.value as FormRole }))} disabled={formLoading}>
                  {availableRoles.map((r) => (
                    <option key={r} value={r}>{ROLE_LABEL[r]}</option>
                  ))}
                </select>
              </label>
              {(isCompany || modal.mode === "edit") && floors.length > 0 && (
                <label className={styles.field}>
                  <span className={styles.fieldLabel}>
                    {modal.mode === "edit" ? "Transfer to floor" : "Floor"}
                  </span>
                  <select
                    className={styles.select}
                    value={formState.floor_id}
                    onChange={(e) => setFormState((s) => ({ ...s, floor_id: e.target.value }))}
                    disabled={formLoading}
                  >
                    <option value="">— No floor —</option>
                    {floorOptions.map((f) => (
                      <option key={f.floor_id} value={f.floor_id}>{f.name}</option>
                    ))}
                  </select>
                  {modal.mode === "edit" && formState.floor_id && formState.floor_id !== (modal.user.floor_id ?? "") && (
                    <p className={styles.fieldHint}>
                      This will initiate a transfer request — user status becomes Pending until approved.
                    </p>
                  )}
                </label>
              )}
              {modal.mode === "edit" && (
                <label className={styles.field}>
                  <span className={styles.fieldLabel}>Status</span>
                  <select className={styles.select} value={formState.status} onChange={(e) => setFormState((s) => ({ ...s, status: e.target.value as FormStatus }))} disabled={formLoading}>
                    <option value="active">Active</option>
                    <option value="disabled">Disabled</option>
                    <option value="pending">Pending</option>
                  </select>
                </label>
              )}
            </div>
            <div className={styles.modalActions}>
              <button className={styles.secondaryButton} type="button" disabled={formLoading} onClick={() => setModal(null)}>Cancel</button>
              <button className={styles.primaryButton} type="button" disabled={formLoading} onClick={handleSave}>
                {formLoading ? <><Loader2 size={14} className={styles.spinner} /> Saving…</> : modal.mode === "create" ? "Create user" : "Save changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
