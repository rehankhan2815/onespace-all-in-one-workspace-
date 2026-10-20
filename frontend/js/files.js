document.addEventListener("DOMContentLoaded", async function () {
  if (!window.OneSpaceAuth.requireAuth()) return;

  const workspaceId = window.OneSpaceUtils.getQueryParam("workspace_id");
  if (!workspaceId) {
    window.location.replace("workspaces.html");
    return;
  }

  document.querySelectorAll("[data-nav]").forEach(function (link) {
    const page = link.getAttribute("data-nav");
    link.href = `${page}.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  });
  document.getElementById("dashboardLink").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  document.getElementById("backDashboard").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async function () {
      await window.OneSpaceAuth.logout();
      window.location.replace("login.html");
    });
  }

  const filesBody = document.getElementById("filesBody");
  const filesEmpty = document.getElementById("filesEmpty");
  const filesTable = document.getElementById("filesTable");
  const uploadFileBtn = document.getElementById("uploadFileBtn");
  const emptyUploadFileBtn = document.getElementById("emptyUploadFileBtn");
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  async function loadFiles() {
    try {
      const files = await window.OneSpaceAPI.getFiles(workspaceId);
      renderFiles(files);
    } catch (err) {
      window.OneSpaceUtils.showError(err.message || "Failed to load files");
    }
  }

  function renderFiles(files) {
    if (!files.length) {
      filesBody.innerHTML = "";
      filesTable.classList.add("d-none");
      filesEmpty.classList.remove("d-none");
      filesEmpty.classList.remove("hidden");
      return;
    }
    filesTable.classList.remove("d-none");
    filesEmpty.classList.add("d-none");
    filesBody.innerHTML = files.map(function (f) {
      const size = window.OneSpaceUtils.formatFileSize(f.size);
      return `
        <tr data-id="${f.id}" class="hover:bg-surface-container-low/50 transition-colors">
          <td class="px-md py-sm">
            <div class="d-flex align-items-center">
              <i class="bi bi-file-earmark text-secondary me-2 fs-5"></i>
              <span class="font-medium">${window.OneSpaceUtils.escapeHtml(f.filename)}</span>
            </div>
          </td>
          <td class="px-md py-sm hidden sm:table-cell text-muted">${size}</td>
          <td class="px-md py-sm hidden md:table-cell text-muted">${window.OneSpaceUtils.formatRelativeTime(f.upload_date)}</td>
          <td class="px-md py-sm text-end">
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-secondary download-btn" disabled title="Download unavailable in mock mode" aria-label="Download unavailable">
                <i class="bi bi-download"></i>
              </button>
              <button type="button" class="btn btn-outline-danger delete-btn" data-id="${f.id}" aria-label="Delete file">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");

    filesBody.querySelectorAll(".delete-btn").forEach(function (btn) {
      btn.addEventListener("click", function () { deleteFile(this.dataset.id); });
    });
  }

  function triggerFilePicker() {
    fileInput.value = "";
    fileInput.click();
  }

  fileInput.addEventListener("change", async function () {
    const file = fileInput.files[0];
    if (!file) return;
    try {
      await window.OneSpaceAPI.createMockFile(workspaceId, {
        filename: file.name,
        size: file.size
      });
      window.OneSpaceUtils.showSuccess(`File "${file.name}" added (mock)`);
      loadFiles();
    } catch (err) {
      window.OneSpaceUtils.showError(err.message);
    }
  });

  uploadFileBtn.addEventListener("click", triggerFilePicker);
  emptyUploadFileBtn.addEventListener("click", triggerFilePicker);

  async function deleteFile(fileId) {
    if (!confirm("Delete this file? This cannot be undone.")) return;
    try {
      await window.OneSpaceAPI.deleteFile(workspaceId, fileId);
      window.OneSpaceUtils.showSuccess("File deleted");
      loadFiles();
    } catch (err) {
      window.OneSpaceUtils.showError(err.message);
    }
  }

  loadFiles();
});