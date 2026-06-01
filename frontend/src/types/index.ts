export type ApiError = {
	error: {
		code: string;
		message: string;
		details: unknown | null;
	};
};

export type AuthUser = {
	user_id: string;
	organization_id: string;
	email: string;
	full_name: string;
	role: "admin" | "manager" | "user";
	status: "active" | "disabled" | "pending";
	last_login_at: string | null;
	created_at: string;
	updated_at: string;
};

export type AuthResponse = {
	user: AuthUser;
	access_token: string;
	token_type: "Bearer";
	expires_in: number;
};

export type FileItem = {
	file_id: string;
	organization_id: string;
	owner_user_id: string;
	owner_name: string;
	uploaded_by_user_id: string;
	original_name: string;
	mime_type: string;
	size_bytes: number;
	sha256: string;
	encryption_algorithm: "AES-256-GCM";
	vault_type: "general" | "private";
	publish_status: "pending" | "published" | "rejected" | "na";
	reviewed_by_user_id: string | null;
	reviewed_at: string | null;
	review_note: string | null;
	status: "active" | "deleted" | "quarantined";
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
};

export type FileListResponse = {
	items: FileItem[];
	page: number;
	page_size: number;
	total: number;
};

export type FileDeleteResponse = {
	success: boolean;
	deleted_file_id: string;
};

export type AuditLogItem = {
	audit_id: string;
	organization_id: string;
	actor_user_id: string;
	actor_name: string;
	action: string;
	resource_type: string;
	resource_id: string | null;
	result: "success" | "denied" | "error";
	reason: string | null;
	created_at: string;
};

export type AuditLogListResponse = {
	items: AuditLogItem[];
	page: number;
	page_size: number;
	total: number;
};

export type PublishRequestItem = {
	request_id: string;
	organization_id: string;
	file_id: string;
	file_name: string;
	requester_user_id: string;
	requester_name: string;
	status: "pending" | "approved" | "rejected";
	reviewed_by_user_id: string | null;
	reviewed_at: string | null;
	review_note: string | null;
	created_at: string;
	updated_at: string;
};

export type PublishRequestListResponse = {
	items: PublishRequestItem[];
	total: number;
};

export type UserItem = {
	user_id: string;
	organization_id: string;
	email: string;
	full_name: string;
	role: "admin" | "manager" | "user";
	status: "active" | "disabled" | "pending";
	last_login_at: string | null;
	created_at: string;
	updated_at: string;
};

export type UserListResponse = {
	items: UserItem[];
	page: number;
	page_size: number;
	total: number;
};
