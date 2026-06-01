"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  KeyRound,
  Loader2,
  ShieldCheck,
} from "lucide-react";

import { buildApiUrl } from "../../lib/api";
import { setAccessToken } from "../../lib/auth";
import type { ApiError, AuthResponse } from "../../types";

import styles from "./auth-screen.module.css";

export type AuthViewState = "default" | "loading" | "error" | "success";

export function AuthScreen() {
  const router = useRouter();
  const [viewState, setViewState] = useState<AuthViewState>("default");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isLoading = viewState === "loading";
  const isError = viewState === "error";

  function resolveError(code?: string, message?: string): string {
    const map: Record<string, string> = {
      invalid_credentials: "Email or password is incorrect.",
      account_disabled: "This account is disabled. Contact your administrator.",
      invalid_payload: "Please check your inputs and try again.",
      validation_error: "Please check your inputs and try again.",
      unauthorized: "Your session expired. Please sign in again.",
    };
    return map[code ?? ""] ?? message ?? "Authentication failed. Please try again.";
  }

  async function submitAuth(endpoint: string, payload: Record<string, string>) {
    setViewState("loading");
    setErrorMessage(null);
    try {
      const response = await fetch(buildApiUrl(endpoint), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = (await response.json().catch(() => null)) as AuthResponse | ApiError | null;
      if (!response.ok) {
        const err = data as ApiError | null;
        setErrorMessage(resolveError(err?.error?.code, err?.error?.message));
        setViewState("error");
        return;
      }
      const auth = data as AuthResponse;
      setAccessToken(auth.access_token);
      setViewState("success");
      router.push("/dashboard");
    } catch {
      setErrorMessage("Could not reach the server. Check your connection.");
      setViewState("error");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) return;
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    if (!email || !password) {
      setErrorMessage("Email and password are required.");
      setViewState("error");
      return;
    }
    await submitAuth("/api/auth/login", { email, password });
  }

  if (viewState === "success") {
    return (
      <main className={styles.screen}>
        <section className={styles.shell}>
          <div className={styles.successCard}>
            <div className={styles.successIcon}>
              <CheckCircle2 size={32} />
            </div>
            <h1 className={styles.successTitle}>Access confirmed</h1>
            <p className={styles.successText}>Redirecting to your vault…</p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.screen}>
      <section className={styles.shell}>
        <header className={styles.header}>
          <div className={styles.logo}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <p className={styles.logoLabel}>Secure Enterprise Data Vault</p>
          </div>
        </header>

        <article className={styles.card}>
          <div className={styles.cardTitle}>
            <KeyRound size={20} className={styles.cardTitleIcon} />
            <h1 className={styles.title}>Sign in</h1>
          </div>
          <p className={styles.subtitle}>
            Use your organization credentials to access the vault.
          </p>

          {isError && (
            <div className={styles.errorBanner} role="alert">
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          <form className={styles.form} onSubmit={handleSubmit} noValidate>
            <label className={styles.field}>
              <span className={styles.label}>Email</span>
              <input
                className={styles.input}
                type="email"
                name="email"
                placeholder="name@company.com"
                autoComplete="email"
                disabled={isLoading}
                aria-invalid={isError}
              />
            </label>

            <label className={styles.field}>
              <span className={styles.label}>Password</span>
              <input
                className={styles.input}
                type="password"
                name="password"
                placeholder="Password"
                autoComplete="current-password"
                disabled={isLoading}
                aria-invalid={isError}
              />
            </label>

            <button className={styles.primaryButton} type="submit" disabled={isLoading}>
              {isLoading ? (
                <><Loader2 size={16} className={styles.spinner} /> Signing in…</>
              ) : (
                <><ArrowRight size={16} /> Sign in</>
              )}
            </button>
          </form>

          <footer className={styles.cardFooter}>
            <ShieldCheck size={14} />
            <span>AES-256 encrypted storage. Every action is audit-logged.</span>
          </footer>
        </article>
      </section>
    </main>
  );
}

export default AuthScreen;
