# OneSpace — Backend Handoff Document

This document is the complete contract for the backend and database design teams.
The frontend is **fully functional today using browser localStorage (mock mode)**.
Your job is to implement the real API that replaces the mock data layer.

---

## 1. Project Overview

OneSpace is a small product-management app organized around **workspaces**. Each
workspace holds **tasks, notes, resources, and files**, plus an **activity log**.
There is also a **global search** across a workspace.

The frontend is pure HTML/CSS/vanilla JS (no build step). Every server call is
already stubbed in `js/api.js` — the backend team only needs to implement the
endpoints below and flip one config flag.

---

## 2. Tech Stack (Frontend)

| Layer | Technology |
|---|---|
| Language | Vanilla JavaScript (ES6+), HTML5, CSS3 |
| Styling | Tailwind CSS (CDN) + custom CSS |
| Augmenting JS | Bootstrap 5.3 JS bundle (modals, toasts only — **no Bootstrap CSS**) |
| Icons | Material Symbols Outlined |
| Network | `fetch` API, JSON payloads |
| Storage (mock) | Browser `localStorage` |
| Auth | Bearer token sent as `Authorization` header |

No build tools, no npm, no framework. Files are loaded via plain `<script>` tags.

---

## 3. Mock Mode vs Real Mode

The switch is in `js/config.js`:

```js
// js/config.js
window.OneSpaceConfig = {
  API_BASE_URL: "",      // e.g. "https://api.example.com"
  USE_MOCK_DATA: true    // change to false to hit the real backend
};
```

- `USE_MOCK_DATA: true` → all reads/writes go to `localStorage`.
- `USE_MOCK_DATA: false` → every call is a real `fetch` to the backend.

`js/api.js` wraps every operation with `withMockData(mockFn, realFn)`. The `realFn`
is the actual HTTP call the backend must serve. The endpoint paths below are taken
verbatim from those `realFn` implementations.

The mock data seed lives in `js/mock-data.js` and runs automatically on first
login/register (it seeds users, workspaces, tasks, notes, resources, files, activity).
The seed JSON doubles as the **reference schema** — use it as the source of truth
for field names and data shapes.

---

## 4. Authentication

### Flow
1. User registers → a user record is created.
2. User logs in → backend returns an **auth token**.
3. Frontend stores the token in `localStorage` under key `onespace_auth` as JSON:
   ```json
   { "token": "...", "userId": "...", "userEmail": "...", "createdAt": "..." }
   ```
4. Every subsequent request sends the token header:
   ```
   Authorization: Bearer <token>
   ```
5. `js/auth.js` `requireAuth()` redirects to `login.html` when there is no token.

### Validation enforced by the frontend
- Email must match `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`.
- Password must be **at least 6 characters**.
- Register requires `name`, `email`, `password`, `confirmPassword`; passwords must match.

### Notes for backend
- Storing plaintext passwords is unacceptable — use a hasher (e.g. bcrypt/argon2).
- `getCurrentUser()` reads `userId`/`userEmail` from the stored auth record; returning
  the user profile from a token endpoint is acceptable.
- Login accepts **email OR username** — the mock checks `email` or `name` case-insensitively.

---

## 5. Complete API Contract

**Base URL**: configured via `js/config.js` → `API_BASE_URL`.
**Headers**: `Authorization: Bearer <token>` on all authenticated requests.
**Content-Type**: `application/json` on requests with a body.

> Response format: the frontend accesses the raw JSON body. To maximize compatibility,
> either return the entity directly (`{ "id": "...", "name": "..." }`) or wrapped in a
> `data` key (`{ "data": { ... } }`) — the frontend automatically unwraps a top-level
> `data` key if present. For errors, return a non-2xx status with a `message` field.

### 5.1 Auth

| Method | Path | Body | Success |
|---|---|---|---|
| `POST` | `/api/auth/login/` | `{ "email": String, "password": String }` | `{ token, user: { id, name, email } }` |
| `POST` | `/api/auth/register/` | `{ "name": String, "email": String, "password": String }` | `{ success, user }` |

### 5.2 Workspaces

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/` | — | Array of workspaces |
| `POST` | `/api/workspaces/` | `{ "name": String (req), "description": String (opt) }` | Created workspace |
| `PATCH` | `/api/workspaces/{id}/` | Any of: `name`, `description`, `archived` | Updated workspace |
| `POST` | `/api/workspaces/{id}/archive/` | — | Updated workspace (sets `archived: true`) |
| `DELETE` | `/api/workspaces/{id}/` | — | `true`/success |

### 5.3 Tasks

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/tasks/` | — | Array of tasks |
| `POST` | `/api/workspaces/{id}/tasks/` | `{ "title": String (req), "description": String, "status": String, "priority": String, "due_date": String }` | Created task |
| `PATCH` | `/api/workspaces/{id}/tasks/{taskId}/` | Any subset of task fields | Updated task |
| `DELETE` | `/api/workspaces/{id}/tasks/{taskId}/` | — | `true`/success |

### 5.4 Notes

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/notes/` | — | Array of notes |
| `POST` | `/api/workspaces/{id}/notes/` | `{ "title": String (req), "body": String (opt) }` | Created note |
| `PATCH` | `/api/workspaces/{id}/notes/{noteId}/` | Any subset of note fields | Updated note |
| `DELETE` | `/api/workspaces/{id}/notes/{noteId}/` | — | `true`/success |

### 5.5 Resources

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/resources/` | — | Array of resources |
| `POST` | `/api/workspaces/{id}/resources/` | `{ "title": String (req), "url": String, "description": String }` | Created resource |
| `PATCH` | `/api/workspaces/{id}/resources/{resourceId}/` | Any subset of resource fields | Updated resource |
| `DELETE` | `/api/workspaces/{id}/resources/{resourceId}/` | — | `true`/success |

### 5.6 Files

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/files/` | — | Array of files |
| `POST` | `/api/workspaces/{id}/files/` | `{ "filename": String (req), "size": Number }` | Created file |
| `DELETE` | `/api/workspaces/{id}/files/{fileId}/` | — | `true`/success |

> Note: file **upload** is currently simulated in the frontend — it sends filename +
> size only (no raw binary). Actual multipart upload can be introduced later; the
> mock `createMockFile` stores `filename` and `size`.

### 5.7 Activity

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/activity/` | — | Array of activity entries |

### 5.8 Search

| Method | Path | Body / Params | Success |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/search/?q={query}` | query string `q` | Object with `{ tasks, notes, resources, files }` arrays |

> Search is case-insensitive substring matching across: task `title`/`description`/
> `status`/`priority`, note `title`/`body`, resource `title`/`description`/`url`,
> file `filename`. An empty `q` returns empty arrays.

---

## 6. Database Schema

Data model mirrored from `js/mock-data.js`. All `*_at` fields are ISO-8601 strings.

### users

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `user-demo` |
| `name` | String | Full name; also usable as login identifier |
| `email` | String (unique) | Lowercased at login |
| `password` | String | **Backend: store hashed, never plaintext** |

### workspaces

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `ws-design` |
| `name` | String (required) | Max 200 chars in UI |
| `description` | String (nullable) | Max 500 chars in UI |
| `created_at` | DateTime | ISO-8601 |
| `updated_at` | DateTime | ISO-8601 |
| `archived` | Boolean | Default `false`; archived items omitted from some views |
| `owner_id` / `created_by` | FK → users | **OPEN DECISION — see §7** |

### tasks

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `task-1` |
| `workspace_id` | FK → workspaces | Cascades on workspace delete |
| `title` | String (required) | |
| `description` | String (nullable) | |
| `status` | Enum | One of `To Do`, `In Progress`, `Done` |
| `priority` | Enum | One of `Low`, `Medium`, `High` |
| `due_date` | Date (nullable) | `YYYY-MM-DD` in mock |
| `created_at` | DateTime | ISO-8601 |
| `updated_at` | DateTime | ISO-8601 |

### notes

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `note-1` |
| `workspace_id` | FK → workspaces | Cascades on workspace delete |
| `title` | String (required) | |
| `body` | Text (nullable) | |
| `created_at` | DateTime | ISO-8601 |
| `updated_at` | DateTime | ISO-8601 |

### resources

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `resource-1` |
| `workspace_id` | FK → workspaces | Cascades on workspace delete |
| `title` | String (required) | |
| `url` | String (nullable) | Validated as URL in UI |
| `description` | String (nullable) | |
| `created_at` | DateTime | ISO-8601 |
| `updated_at` | DateTime | ISO-8601 |

### files

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `file-1` |
| `workspace_id` | FK → workspaces | Cascades on workspace delete |
| `filename` | String (required) | |
| `size` | Number | Bytes |
| `upload_date` | DateTime | ISO-8601 |

### activity

| Field | Type | Notes |
|---|---|---|
| `id` | String (PK) | e.g. `activity-1` |
| `workspace_id` | FK → workspaces | Cascades on workspace delete |
| `type` | String | e.g. `task_updated`, `note_updated`, `resource_added`, `file_uploaded`, `task_completed` |
| `message` | String | Human-readable summary |
| `timestamp` | DateTime | ISO-8601 |

---

## 7. Data Relationships

```
users
  └─ (owner/creator of) 1──N  workspaces         [! ownership not in current mock — decide below]

workspaces 1──N tasks
workspaces 1──N notes
workspaces 1──N resources
workspaces 1──N files
workspaces 1──N activity

tasks     ── belongs to workspace
notes     ── belongs to workspace
resources ── belongs to workspace
files     ── belongs to workspace
activity  ── belongs to workspace
```

### Deleting a workspace
The frontend (`deleteWorkspace`) expects the backend to **cascade-delete all**
dependent tasks, notes, resources, files, and activity for that workspace.

### OPEN DECISION — ownership model
The current mock data has **no owner field** on workspaces (or child records).
The frontend lists all workspaces for the logged-in user with no filtering.
Decision required:

1. **Single-user-per-workspace**: add `owner_id` (or `created_by`) to `workspaces`,
   filter `GET /api/workspaces/` to the current user.
2. **Shared/multi-user workspaces**: introduce a `workspace_members` join table
   (workspace_id, user_id, role). Frontend currently has no member UI, but a
   members table is future-proof.

Option 2 is recommended if collaboration is on the roadmap; option 1 matches the
current frontend exactly.

---

## 8. Database Design Notes (for the DB designer)

- **Index `workspace_id`** on `tasks`, `notes`, `resources`, `files`, `activity`
  (all reads are filtered by workspace).
- **Add an index on `workspaces.id`** and `users.email` (unique).
- `status` / `priority` / `type` are short enums → use `ENUM` or a lookup table;
  keep the exact string values shown above (frontend renders them literally).
- `due_date`: store as `DATE`.
- All IDs in the mock are readable slugs (`ws-design`, `task-1`). The frontend uses
  them as opaque strings — you may use **numeric auto-increment** or **UUIDs**; the
  frontend never depends on ID format. The `PATCH`/`DELETE` URLs simply interpolate
  the ID (URL-encoded).
- Timestamps: return ISO-8601 strings. The frontend parses them with `new Date(...)`.
- Deleting a file should also delete the physical file on the storage backend.

---

## 9. Demo Credentials (mock data)

These seed the mock storage on first login:

| Email | Password |
|---|---|
| `demo@onespace.test` | `demo123` |
| `alex@onespace.test` | `alex123` |

If you want to quick-test without registration, seed one of these users.

---

## 10. Files the Backend Team Needs to Know

| File | Purpose |
|---|---|
| `js/config.js` | `API_BASE_URL` + `USE_MOCK_DATA` toggle |
| `js/api.js` | **All endpoint definitions & request/response shapes (real HTTP calls live here)** |
| `js/mock-data.js` | Reference seed data / schema truth |
| `js/auth.js` | Auth/token handling, `requireAuth()` |
| `js/utils.js` | `showToast`, `formatDate`, `debounce`, `escapeHtml` |
| `js/workspaces.js` | Workspace CRUD + navigation |
| `js/dashboard.js` | Dashboard summaries & recent lists |
| `js/tasks.js` | Task CRUD + filters + inline status |
| `js/notes.js` | Note CRUD |
| `js/resources.js` | Resource CRUD |
| `js/files.js` | File list/upload/delete |
| `js/search.js` | Debounced global search |
| `js/login.js`, `js/register.js` | Auth form handling |

---

## 11. Frontend Validation Rules (backend should mirror)

| Entity | Rule |
|---|---|
| Login | email/username + password both required |
| Register | name, email, password (≥6 chars), confirm match; email unique |
| Workspace | `name` required (≤200), `description` optional (≤500) |
| Task | `title` required; `status`, `priority`, `due_date` optional strings |
| Note | `title` required |
| Resource | `title` required; `url` must be a valid URL format |
| File | `filename` required |

On validation failure, the frontend shows the server's `message` — return a clear
error message with a non-2xx status.