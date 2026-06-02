# System Architecture

SEDV follows a multi-tenant enterprise architecture where data, permissions, documents, and audit logs are isolated by organizational floor while remaining centrally governed by Company administrators.

## Hierarchy

```text
Company
│
├── Floor 1 (Business Operations)
│   ├── Admin
│   ├── Manager
│   └── User
│
└── Floor 2 (Engineering)
    ├── Admin
    ├── Manager
    └── User
```

## Access Model

### Company

Global administrator with unrestricted access.

Capabilities:

* Manage all users across all floors
* Full CRUD on personnel
* Access all documents
* Access all audit logs
* Configure floor assignments and roles

### Floor Admin

Administrator scoped to a single floor.

Capabilities:

* Manage Users and Managers within their floor
* Promote User → Manager
* Demote Manager → User
* Reset username/password
* Enable or disable accounts
* Review company-level publication requests
* View floor-specific audit logs

Restrictions:

* Cannot access other floors
* Cannot manage Company accounts

### Manager

Department-level supervisor.

Capabilities:

* Review floor publication requests
* Manage department documents
* View department activity logs

### User

Standard employee account.

Capabilities:

* Upload private documents
* Submit publication requests
* Access approved documents
* View personal activity logs

---

## Floor Isolation

Every resource belongs to exactly one scope:

```text
Floor 1
Floor 2
Company
```

Rules:

* Floor 1 cannot access Floor 2 resources
* Floor 2 cannot access Floor 1 resources
* Floor Admins are restricted to their assigned floor
* Audit logs are isolated by scope
* UI displays floor tags for visibility

---

## Vault Structure

The document vault is divided into three visibility levels.

### Floor Vault

Department and floor-level documents.

Rules:

* Visible only within the owning floor
* Requires approval before publication
* Tagged with the corresponding floor

### Company Vault

Organization-wide documents.

Rules:

* Visible to all floors
* Published through Company approval workflow
* Tagged as Company

### Private Vault

Personal user documents.

Rules:

* Visible only to the owner
* Not accessible by other users
* Requires approval before becoming public

---

## Publication Workflow

### Publish to Floor

```text
User
  ↓
Request Publication
  ↓
Manager Review
  ↓
Approved
  ↓
Floor Vault
```

Rejected submissions are permanently removed from the system.

### Publish to Company

```text
User
  ↓
Request Publication
  ↓
Floor Admin Review
  ↓
Approved
  ↓
Company Vault
```

Approved documents become available to all floors.

---

## Cross-Floor Sharing

Documents are private to their floor by default.

```text
Floor Document
      ↓
Sharing Request
      ↓
Floor Admin Approval
      ↓
Company Synchronization
      ↓
Visible Across Floors
```

All sharing actions are recorded in the audit log.

---

## Audit Logging

Every security-sensitive action is recorded.

Tracked events include:

* Login / Logout
* Upload Document
* Delete Document
* Publish Request
* Approval / Rejection
* User Management
* Password Reset

Log entries contain:

* Action
* Actor
* Timestamp
* Result (Success / Failed)

Visibility:

* User → own logs only
* Manager → department logs
* Floor Admin → floor logs
* Company → all logs

---

## Security Principles

* Role-Based Access Control (RBAC)
* Floor-Level Isolation
* Least Privilege Access
* Approval-Based Publishing
* Full Auditability
* Multi-Level Document Visibility
