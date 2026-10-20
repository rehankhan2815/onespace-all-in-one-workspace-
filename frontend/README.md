# OneSpace Frontend

A centralized, project‑based **work‑context management** web application built entirely with **HTML5, CSS3, and vanilla JavaScript (ES6+)**. No build tools, no frameworks, no backend – all data is persisted in `localStorage` via a clean API layer that can later be swapped for a real Django REST Framework backend.

---

## Features

- **Mock authentication** (login / register / logout) with token stored in `localStorage`.
- **Workspaces**: create, list, archive, delete (cascades to child resources).
- **Tasks**: full CRUD, status/priority/due‑date, inline status change, filters, search.
- **Notes**: rich cards with title/body, timestamps, edit/delete.
- **Resources**: title, URL, description, open in new tab, validation.
- **Files**: mock upload (file picker captures name/size only), list, delete, download disabled with tooltip.
- **Compiler**: write and run Python in the browser (Pyodide, loaded on demand from CDN) with stdout/stderr capture, error traces, and Ctrl/Cmd + Enter.
- **Saved programs**: name, save, load, rename, and delete programs per workspace from a dropdown on the Compiler page; unsaved changes prompt before leaving.
- **Dashboard**: summary cards, recent items per module, recent activity feed.
- **Global search**: debounced, case‑insensitive across tasks, notes, resources, files; grouped results with navigation.
- **Responsive UI**: works on mobile, tablet, desktop; Bootstrap 5 components throughout.
- **Accessibility**: labels on every input, `aria-label` on icon‑only buttons, focus trapping in modals (Bootstrap default), colour + text for status.
- **Loading / empty / error / success states** on every async operation.

---

## Technology Stack

| Layer | Choice |
|-------|--------|
| Markup | HTML5 |
| Styling | CSS3 + **Bootstrap 5.3** (CDN) + **Bootstrap Icons** (CDN) |
| Scripting | Vanilla **JavaScript ES6+** (no modules, plain `<script>` tags) |
| Persistence | `localStorage` (seeded once from `mock-data.js`) |
| Build / bundler | **None** – serve statically via `python serve.py` and visit http://localhost:8080 |

---

## Folder Structure

```
onespace-frontend/
├── login.html
├── register.html
├── workspaces.html
├── dashboard.html
├── tasks.html
├── notes.html
├── resources.html
├── files.html
├── search.html
├── compiler.html
├── README.md
├── css/
│   ├── style.css
│   ├── auth.css
│   └── dashboard.css
├── js/
│   ├── config.js
│   ├── utils.js
│   ├── mock-data.js
│   ├── auth.js
│   ├── api.js
│   ├── login.js
│   ├── register.js
│   ├── workspaces.js
│   ├── dashboard.js
│   ├── tasks.js
│   ├── notes.js
│   ├── resources.js
│   ├── files.js
│   ├── search.js
│   └── compiler.js
└── assets/
```

---

## How to Run

1. Clone or download this folder.
2. Start the local frontend server (requires Python 3, already installed on most systems):
   ```bash
   python serve.py
   ```
3. Open **http://localhost:8080** in your browser — it takes you straight to the login page.
   - Custom port: `python serve.py 5500` → http://localhost:5500
4. Log in with the seeded credentials:
   - **Email:** `demo@onespace.test` **Password:** `demo123`
   - **Email:** `alex@onespace.test` **Password:** `alex123`
5. Or click **"Create one"** to register a new account.

All data is stored in your browser’s `localStorage` under the keys listed below.

---

## Mock Authentication

- `OneSpaceAuth.login(identifier, password)` validates against the seeded users, generates a token like `mock-token-<timestamp>-<random>`, stores it in `localStorage` (`onespace_auth`), and redirects to `workspaces.html`.
- `OneSpaceAuth.isAuthenticated()` checks for the token.
- Guarded pages (`workspaces.html`, `dashboard.html`, …) call `OneSpaceAuth.requireAuth()` on load; missing token redirects to `login.html`.
- **This is explicitly mock authentication** – no hashing, no secure transport. UI copy never claims real security.

---

## Mock Data & `localStorage` Behaviour

On first load each collection key is checked; if absent it is seeded from `js/mock-data.js`. **Existing data is never overwritten.**

| Key | Seeded from | Description |
|-----|-------------|-------------|
| `onespace_users` | `mock-data.js` → `users` | `id, name, email, password` |
| `onespace_workspaces` | `workspaces` | `id, name, description, created_at, updated_at, archived` |
| `onespace_tasks` | `tasks` | `id, workspace_id, title, description, status, priority, due_date, created_at, updated_at` |
| `onespace_notes` | `notes` | `id, workspace_id, title, body, created_at, updated_at` |
| `onespace_resources` | `resources` | `id, workspace_id, title, url, description, created_at, updated_at` |
| `onespace_files` | `files` | `id, workspace_id, filename, upload_date, size` |
| `onespace_snippets` | — (not seeded; created on first save) | `id, workspace_id, title, language, code, created_at, updated_at` |
| `onespace_activity` | `activity` | `id, workspace_id, type, message, timestamp` |
| `onespace_auth` | created on login | `token, userId, userEmail, createdAt` |

All CRUD operations read/write these keys via `OneSpaceAPI` – **page scripts never touch `localStorage` directly**.

---

## Page‑by‑Page Description

| Page | Purpose | Key Interactions |
|------|---------|------------------|
| `login.html` | Email/username + password → token → `workspaces.html` | Enter submits, toggle password visibility, validation |
| `register.html` | Name, email, password, confirm → creates user → redirect to login | Duplicate email check, password match, password toggle |
| `workspaces.html` | Card grid of workspaces; create/archive/delete modals | Open → `dashboard.html?workspace_id=…` |
| `dashboard.html` | Summary cards, recent tasks/notes/resources/files/activity | All links preserve `workspace_id` |
| `tasks.html` | Table with filters, inline status select, add/edit modal, delete | Quick status change, search, priority badges |
| `notes.html` | Cards with preview, add/edit/delete modals | Full body on edit, timestamps |
| `resources.html` | Cards with link button, add/edit/delete modals | URL validation, `target="_blank" rel="noopener noreferrer"` |
| `files.html` | Table, mock upload (file picker), delete, download disabled | Shows “Download unavailable in mock mode” tooltip |
| `search.html` | Single input, debounced, grouped results, navigation | Highlights matches, empty state |
| `compiler.html` | Code editor + output panel for running Python | Language select, Run (Pyodide), saved‑programs dropdown, Save/Rename/Delete, unsaved‑changes prompt on exit |

---

## Architecture – `OneSpaceAPI` Isolation Pattern

```
Page script (e.g. tasks.js)
        │
        ▼
OneSpaceAPI.getTasks(workspaceId)   ◄───►  OneSpaceAPI.updateTask(...)
        │                                    (all methods return Promises)
        ▼
┌─────────────────────────────────────────┐
│  OneSpaceConfig.USE_MOCK_DATA = true   │
│  (config.js)                            │
└─────────────────────────────────────────┘
        │
        ▼
Mock implementation reads/writes localStorage
        │
        ▼
Returns cloned data → UI updates
```

**Future swap:** set `OneSpaceConfig.USE_MOCK_DATA = false` and implement the real `fetch` branches inside `api.js` (already stubbed). No page script changes required.

---

## Future Django REST API Contract

All endpoints require authentication (`Authorization: Bearer <token>`). Responses follow a consistent envelope:

**Success**
```json
{ "success": true, "data": { … }, "message": "Optional human‑readable message" }
```

**Error**
```json
{ "success": false, "message": "Human readable error", "errors": { "field": "detail" } }
```

### Authentication
| Method | Path | Purpose | Request | Success Response |
|--------|------|---------|---------|------------------|
| POST | `/api/auth/login/` | Obtain token | `{ "email": "…", "password": "…" }` | `{ "success": true, "data": { "token": "…", "user": { "id": "…", "name": "…", "email": "…" } } }` |
| POST | `/api/auth/register/` | Create account | `{ "name": "…", "email": "…", "password": "…", "password_confirm": "…" }` | `{ "success": true, "data": { "user": { … } }, "message": "Account created" }` |
| POST | `/api/auth/logout/` | Invalidate token (optional) | `{}` | `{ "success": true, "message": "Logged out" }` |

### Workspaces
| Method | Path | Purpose | Request | Success Response |
|--------|------|---------|---------|------------------|
| GET | `/api/workspaces/` | List all workspaces | – | `{ "success": true, "data": [ { "id", "name", "description", "created_at", "updated_at", "archived" } ] }` |
| POST | `/api/workspaces/` | Create workspace | `{ "name": "…", "description": "…" }` | `{ "success": true, "data": { workspace object } }` |
| GET | `/api/workspaces/{id}/` | Retrieve workspace | – | `{ "success": true, "data": { workspace object } }` |
| PATCH | `/api/workspaces/{id}/` | Update workspace | `{ "name"?, "description"?, "archived"? }` | `{ "success": true, "data": { updated workspace } }` |
| POST | `/api/workspaces/{id}/archive/` | Archive workspace | `{}` | `{ "success": true, "data": { archived workspace } }` |
| DELETE | `/api/workspaces/{id}/` | Delete workspace (cascades) | – | `{ "success": true, "message": "Workspace deleted" }` |

### Tasks (scoped to workspace)
| Method | Path | Purpose | Request | Success Response |
|--------|------|---------|---------|------------------|
| GET | `/api/workspaces/{workspace_id}/tasks/` | List tasks | Query: `status`, `priority`, `search` | `{ "success": true, "data": [ task objects ] }` |
| POST | `/api/workspaces/{workspace_id}/tasks/` | Create task | `{ "title": "…", "description"?, "status"?, "priority"?, "due_date"?, }` | `{ "success": true, "data": { task object } }` |
| GET | `/api/workspaces/{workspace_id}/tasks/{id}/` | Retrieve task | – | `{ "success": true, "data": { task object } }` |
| PATCH | `/api/workspaces/{workspace_id}/tasks/{id}/` | Update task | Partial task fields | `{ "success": true, "data": { updated task } }` |
| DELETE | `/api/workspaces/{workspace_id}/tasks/{id}/` | Delete task | – | `{ "success": true, "message": "Task deleted" }` |

*(Notes, Resources, Files follow identical CRUD pattern under `/api/workspaces/{workspace_id}/notes/`, `/resources/`, `/files/`. Saved compiler programs follow it too under `/api/workspaces/{workspace_id}/snippets/` — see `BACKEND_HANDOFF.md` §5.9.)*

### Files
| Method | Path | Purpose | Request | Success Response |
|--------|------|---------|---------|------------------|
| GET | `/api/workspaces/{workspace_id}/files/` | List files | – | `{ "success": true, "data": [ file metadata ] }` |
| POST | `/api/workspaces/{workspace_id}/files/` | Upload file (multipart) | `file` + optional fields | `{ "success": true, "data": { file metadata } }` |
| GET | `/api/workspaces/{workspace_id}/files/{id}/download/` | Download file | – | Binary file stream |
| DELETE | `/api/workspaces/{workspace_id}/files/{id}/` | Delete file | – | `{ "success": true, "message": "File deleted" }` |

### Search & Activity
| Method | Path | Purpose | Query Params | Success Response |
|--------|------|---------|--------------|------------------|
| GET | `/api/workspaces/{workspace_id}/search/` | Global search | `q` (string) | `{ "success": true, "data": { "tasks": [], "notes": [], "resources": [], "files": [] } }` |
| GET | `/api/workspaces/{workspace_id}/activity/` | Recent activity | `limit?` | `{ "success": true, "data": [ activity objects ] }` |

---

## Switching to the Real Backend

1. Set `OneSpaceConfig.USE_MOCK_DATA = false` in `js/config.js`.
2. Set `OneSpaceConfig.API_BASE_URL` to your Django API root (e.g. `"https://api.example.com"`).
3. The stubbed `fetch` branches in `api.js` already construct the correct endpoints and include the Bearer token.
4. Ensure your Django REST endpoints match the contract above (or adjust the `requestJson` paths in `api.js`).
5. No changes to any page‑level script (`*.js` except `api.js`) are required.

---

## License

MIT – feel free to use for your college mini‑project.