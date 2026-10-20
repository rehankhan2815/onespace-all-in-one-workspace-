document.addEventListener("DOMContentLoaded", async function () {
  if (!window.OneSpaceAuth.requireAuth()) return;

  const workspaceId = window.OneSpaceUtils.getQueryParam("workspace_id");
  if (!workspaceId) {
    window.location.replace("workspaces.html");
    return;
  }

  // Update all navigation links with workspace_id
  document.querySelectorAll("[data-nav]").forEach(function (link) {
    const page = link.getAttribute("data-nav");
    link.href = `${page}.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  });

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async function () {
      await window.OneSpaceAuth.logout();
      window.location.replace("login.html");
    });
  }

  try {
    const [workspace, tasks, notes, resources, files, activity] = await Promise.all([
      window.OneSpaceAPI.getWorkspaces().then(function (ws) { return ws.find(function (w) { return w.id === workspaceId; }); }),
      window.OneSpaceAPI.getTasks(workspaceId),
      window.OneSpaceAPI.getNotes(workspaceId),
      window.OneSpaceAPI.getResources(workspaceId),
      window.OneSpaceAPI.getFiles(workspaceId),
      window.OneSpaceAPI.getActivity(workspaceId)
    ]);

    if (!workspace) {
      window.location.replace("workspaces.html");
      return;
    }

    renderWorkspaceHeader(workspace);
    renderSummaryCards(workspaceId, tasks, notes, resources, files);
    renderRecentTasks(tasks);
    renderRecentNotes(notes);
    renderRecentResources(resources);
    renderRecentFiles(files);
    renderRecentActivity(activity);
  } catch (err) {
    window.OneSpaceUtils.showError(err.message || "Failed to load dashboard");
  }

  function renderWorkspaceHeader(ws) {
    document.getElementById("workspaceTitle").textContent = ws.name;
    document.getElementById("workspaceName").textContent = ws.name;
    document.getElementById("workspaceDescription").textContent = ws.description || "No description";
  }

  function renderSummaryCards(wsId, tasks, notes, resources, files) {
    const completedTasks = tasks.filter(function (t) { return t.status === "Done"; }).length;
    const pendingTasks = tasks.filter(function (t) { return t.status !== "Done"; }).length;

    const cards = [
      { label: "Total Tasks", value: tasks.length, icon: "bi-kanban", color: "primary", link: `tasks.html?workspace_id=${encodeURIComponent(wsId)}` },
      { label: "Completed", value: completedTasks, icon: "bi-check-circle-fill", color: "success", link: `tasks.html?workspace_id=${encodeURIComponent(wsId)}&status=Done` },
      { label: "Pending", value: pendingTasks, icon: "bi-clock", color: "warning", link: `tasks.html?workspace_id=${encodeURIComponent(wsId)}&status=To Do` },
      { label: "Notes", value: notes.length, icon: "bi-journal-text", color: "info", link: `notes.html?workspace_id=${encodeURIComponent(wsId)}` },
      { label: "Resources", value: resources.length, icon: "bi-link-45deg", color: "primary", link: `resources.html?workspace_id=${encodeURIComponent(wsId)}` },
      { label: "Files", value: files.length, icon: "bi-file-earmark", color: "secondary", link: `files.html?workspace_id=${encodeURIComponent(wsId)}` }
    ];

    const container = document.getElementById("summaryCards");
    container.innerHTML = cards.map(function (c) {
      return `
        <div class="col">
          <a href="${c.link}" class="card text-decoration-none h-100">
            <div class="card-body d-flex align-items-center">
              <div class="icon-bg bg-${c.color} text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 48px; height: 48px;">
                <i class="bi ${c.icon} fs-4"></i>
              </div>
              <div>
                <p class="mb-0 text-muted small">${c.label}</p>
                <h4 class="mb-0">${c.value}</h4>
              </div>
            </div>
          </a>
        </div>
      `;
    }).join("");
  }

  function renderRecentTasks(tasks) {
    const list = document.getElementById("recentTasksList");
    const recent = [...tasks].sort(function (a, b) {
      return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
    }).slice(0, 5);
    if (!recent.length) {
      list.innerHTML = '<div class="list-group-item text-center text-muted py-4">No tasks yet</div>';
      return;
    }
    list.innerHTML = recent.map(function (t) {
      const badgeClass = t.status === "Done" ? "bg-success" : t.status === "In Progress" ? "bg-primary" : "bg-secondary";
      const priorityClass = t.priority === "High" ? "text-danger" : t.priority === "Medium" ? "text-warning" : "text-info";
      return `
        <a href="tasks.html?workspace_id=${encodeURIComponent(workspaceId)}" class="list-group-item list-group-item-action d-flex align-items-center justify-content-between">
          <div>
            <h6 class="mb-1">${window.OneSpaceUtils.escapeHtml(t.title)}</h6>
            <small class="text-muted">${window.OneSpaceUtils.formatRelativeTime(t.updated_at)}</small>
          </div>
          <div class="d-flex align-items-center gap-2">
            <span class="badge ${badgeClass}">${window.OneSpaceUtils.escapeHtml(t.status)}</span>
            <span class="badge bg-light ${priorityClass}">${window.OneSpaceUtils.escapeHtml(t.priority)}</span>
          </div>
        </a>
      `;
    }).join("");
  }

  function renderRecentNotes(notes) {
    const list = document.getElementById("recentNotesList");
    const recent = [...notes].sort(function (a, b) {
      return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
    }).slice(0, 5);
    if (!recent.length) {
      list.innerHTML = '<div class="list-group-item text-center text-muted py-4">No notes yet</div>';
      return;
    }
    list.innerHTML = recent.map(function (n) {
      const preview = window.OneSpaceUtils.escapeHtml(n.body).substring(0, 120) + (n.body.length > 120 ? "…" : "");
      return `
        <a href="notes.html?workspace_id=${encodeURIComponent(workspaceId)}" class="list-group-item list-group-item-action">
          <h6 class="mb-1">${window.OneSpaceUtils.escapeHtml(n.title)}</h6>
          <p class="mb-1 small text-muted">${preview}</p>
          <small class="text-muted">${window.OneSpaceUtils.formatRelativeTime(n.updated_at)}</small>
        </a>
      `;
    }).join("");
  }

  function renderRecentResources(resources) {
    const list = document.getElementById("recentResourcesList");
    const recent = [...resources].sort(function (a, b) {
      return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
    }).slice(0, 5);
    if (!recent.length) {
      list.innerHTML = '<div class="list-group-item text-center text-muted py-4">No resources yet</div>';
      return;
    }
    list.innerHTML = recent.map(function (r) {
      return `
        <a href="resources.html?workspace_id=${encodeURIComponent(workspaceId)}" class="list-group-item list-group-item-action">
          <h6 class="mb-1">${window.OneSpaceUtils.escapeHtml(r.title)}</h6>
          <p class="mb-1 small text-muted">${window.OneSpaceUtils.escapeHtml(r.description || "No description")}</p>
          <small class="text-muted">${window.OneSpaceUtils.formatRelativeTime(r.updated_at)}</small>
        </a>
      `;
    }).join("");
  }

  function renderRecentFiles(files) {
    const list = document.getElementById("recentFilesList");
    const recent = [...files].sort(function (a, b) {
      return new Date(b.upload_date) - new Date(a.upload_date);
    }).slice(0, 5);
    if (!recent.length) {
      list.innerHTML = '<div class="list-group-item text-center text-muted py-4">No files yet</div>';
      return;
    }
    list.innerHTML = recent.map(function (f) {
      const size = window.OneSpaceUtils.formatFileSize(f.size);
      return `
        <div class="list-group-item d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <i class="bi bi-file-earmark text-secondary me-2 fs-5"></i>
            <div>
              <h6 class="mb-1">${window.OneSpaceUtils.escapeHtml(f.filename)}</h6>
              <small class="text-muted">${size} • ${window.OneSpaceUtils.formatRelativeTime(f.upload_date)}</small>
            </div>
          </div>
          <button class="btn btn-sm btn-outline-secondary disabled" title="Download unavailable in mock mode">
            <i class="bi bi-download"></i>
          </button>
        </div>
      `;
    }).join("");
  }

  function renderRecentActivity(activity) {
    const list = document.getElementById("recentActivityList");
    const recent = [...activity].sort(function (a, b) {
      return new Date(b.timestamp) - new Date(a.timestamp);
    }).slice(0, 10);
    if (!recent.length) {
      list.innerHTML = '<div class="list-group-item text-center text-muted py-4">No recent activity</div>';
      return;
    }
    list.innerHTML = recent.map(function (a) {
      let icon = "bi-info-circle";
      if (a.type.includes("task")) icon = "bi-kanban";
      else if (a.type.includes("note")) icon = "bi-journal-text";
      else if (a.type.includes("resource")) icon = "bi-link-45deg";
      else if (a.type.includes("file")) icon = "bi-file-earmark";
      return `
        <div class="list-group-item activity-item">
          <div class="d-flex align-items-start">
            <i class="bi ${icon} text-muted me-2 mt-1"></i>
            <div>
              <p class="mb-1">${window.OneSpaceUtils.escapeHtml(a.message)}</p>
              <small class="text-muted">${window.OneSpaceUtils.formatRelativeTime(a.timestamp)}</small>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }
});