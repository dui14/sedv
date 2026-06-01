"use client";

import type { ForwardRefExoticComponent, ReactNode, RefAttributes } from "react";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  ClipboardCheck,
  Files,
  History,
  LogOut,
  Menu,
  Shield,
  Users,
  X,
} from "lucide-react";

import { apiRequest, authHeaders } from "../../lib/api";
import { clearAccessToken, getAccessToken } from "../../lib/auth";
import type { AuthUser } from "../../types";

import styles from "./app-shell.module.css";

import type { LucideProps } from "lucide-react";

type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, "ref"> & RefAttributes<SVGSVGElement>>;

type NavItem = {
  href: string;
  label: string;
  Icon: LucideIcon;
  roles: AuthUser["role"][];
  badge?: string;
};

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Vault", Icon: Files, roles: ["admin", "manager", "user"] },
  { href: "/approvals", label: "Approval Queue", Icon: ClipboardCheck, roles: ["admin", "manager"] },
  { href: "/users", label: "Users", Icon: Users, roles: ["admin"] },
  { href: "/audit-log", label: "Audit Log", Icon: BarChart3, roles: ["admin", "manager"] },
  { href: "/activity", label: "My Activity", Icon: History, roles: ["user"] },
];

const ROLE_LABEL: Record<AuthUser["role"], string> = {
  admin: "Admin",
  manager: "Manager",
  user: "User",
};

const ROLE_COLOR: Record<AuthUser["role"], string> = {
  admin: styles.roleAdmin,
  manager: styles.roleManager,
  user: styles.roleUser,
};

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    apiRequest<AuthUser>("/api/auth/me", { headers: authHeaders(token) })
      .then(setUser)
      .catch(() => {
        clearAccessToken();
        router.replace("/login");
      });
  }, [router]);

  async function handleLogout() {
    const token = getAccessToken();
    if (token) {
      await apiRequest("/api/auth/logout", {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "user_logout" }),
      }).catch(() => null);
    }
    clearAccessToken();
    router.replace("/login");
  }

  const visibleNav = user ? NAV.filter((item) => item.roles.includes(user.role)) : [];

  const sidebar = (
    <nav className={styles.sidebar} aria-label="Application navigation">
      <div className={styles.sidebarHeader}>
        <div className={styles.brand}>
          <Shield size={18} className={styles.brandIcon} />
          <span className={styles.brandName}>SEDV</span>
        </div>
        <button
          className={styles.sidebarClose}
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        >
          <X size={18} />
        </button>
      </div>

      {user && (
        <div className={styles.userBlock}>
          <div className={styles.userAvatar} aria-hidden="true">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <div className={styles.userInfo}>
            <p className={styles.userName}>{user.full_name}</p>
            <p className={styles.userEmail}>{user.email}</p>
          </div>
          <span className={`${styles.roleBadge} ${ROLE_COLOR[user.role]}`}>
            {ROLE_LABEL[user.role]}
          </span>
        </div>
      )}

      <ul className={styles.navList} role="list">
        {visibleNav.map(({ href, label, Icon }) => {
          const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <li key={href}>
              <a
                href={href}
                className={`${styles.navItem} ${isActive ? styles.navItemActive : ""}`}
                aria-current={isActive ? "page" : undefined}
                onClick={(e) => { e.preventDefault(); setSidebarOpen(false); router.push(href); }}
              >
                <Icon size={17} />
                <span>{label}</span>
              </a>
            </li>
          );
        })}
      </ul>

      <div className={styles.sidebarFooter}>
        <button className={styles.logoutButton} type="button" onClick={handleLogout}>
          <LogOut size={16} />
          <span>Sign out</span>
        </button>
      </div>
    </nav>
  );

  return (
    <div className={styles.shell}>
      <div className={`${styles.sidebarMask} ${sidebarOpen ? styles.sidebarMaskVisible : ""}`} onClick={() => setSidebarOpen(false)} aria-hidden="true" />
      <div className={`${styles.sidebarWrapper} ${sidebarOpen ? styles.sidebarWrapperOpen : ""}`}>
        {sidebar}
      </div>
      <div className={styles.main}>
        <header className={styles.topbar}>
          <button
            className={styles.menuButton}
            type="button"
            aria-label="Open navigation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={20} />
          </button>
          {user && (
            <div className={styles.topbarRight}>
              <span className={`${styles.roleBadgeSmall} ${ROLE_COLOR[user.role]}`}>
                {ROLE_LABEL[user.role]}
              </span>
              <span className={styles.topbarUser}>{user.full_name}</span>
            </div>
          )}
        </header>
        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}
