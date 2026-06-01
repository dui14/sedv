const DEFAULT_API_BASE_URL = process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export function buildApiUrl(path: string): string {
	if (!API_BASE_URL) {
		return path;
	}
	const normalizedBase = API_BASE_URL.endsWith("/") ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
	const normalizedPath = path.startsWith("/") ? path : `/${path}`;
	return `${normalizedBase}${normalizedPath}`;
}

export class ApiClientError extends Error {
	code: string;
	status: number;

	constructor(message: string, code: string, status: number) {
		super(message);
		this.name = "ApiClientError";
		this.code = code;
		this.status = status;
	}
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
	const response = await fetch(buildApiUrl(path), options);
	if (!response.ok) {
		const payload = await response.json().catch(() => null);
		const error = payload?.error;
		throw new ApiClientError(
			error?.message ?? "The request failed.",
			error?.code ?? "request_failed",
			response.status,
		);
	}
	return (await response.json()) as T;
}

export function authHeaders(token: string): HeadersInit {
	return {
		Authorization: `Bearer ${token}`,
	};
}
