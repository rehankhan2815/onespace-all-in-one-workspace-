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
  document.getElementById("dashboardLink").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  document.getElementById("backDashboard").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async function () {
      await window.OneSpaceAuth.logout();
      window.location.replace("login.html");
    });
  }

  const tasksBody = document.getElementById("tasksBody");
  const tasksEmpty = document.getElementById("tasksEmpty");
  const tasksCard = document.getElementById("tasksCard");
  const statusFilter = document.getElementById("statusFilter");
  const priorityFilter = document.getElementById("priorityFilter");
  const searchInput = document.getElementById("searchInput");
  const clearSearch = document.getElementById("clearSearch");
  const addTaskBtn = document.getElementById("addTaskBtn");
  const taskModalEl = document.getElementById("taskModal");
  const taskModal = new bootstrap.Modal(taskModalEl);
  const taskForm = document.getElementById("taskForm");
  const taskIdInput = document.getElementById("taskId");
  const taskTitleInput = document.getElementById("taskTitle");
  const taskDescriptionInput = document.getElementById("taskDescription");
  const taskStatusInput = document.getElementById("taskStatus");
  const taskPriorityInput = document.getElementById("taskPriority");
  const taskDueDateInput = document.getElementById("taskDueDate");
  const taskSubmit = document.getElementById("taskSubmit");
  const taskBtnText = taskSubmit.querySelector(".btn-text");
  const taskBtnLoading = taskSubmit.querySelector(".btn-loading");
  const modalLabel = document.getElementById("taskModalLabel");
  const emptyAddTaskBtn = document.getElementById("emptyAddTaskBtn");

  // Read initial filter from URL params (e.g. from Dashboard cards)
  const initialStatus = window.OneSpaceUtils.getQueryParam("status");
  if (initialStatus && ["To Do", "In Progress", "Done"].includes(initialStatus)) {
    statusFilter.value = initialStatus;
  }
  const initialPriority = window.OneSpaceUtils.getQueryParam("priority");
  if (initialPriority && ["High", "Medium", "Low"].includes(initialPriority)) {
    priorityFilter.value = initialPriority;
  }

  let allTasks = [];

  async function loadTasks() {
    try {
      allTasks = await window.OneSpaceAPI.getTasks(workspaceId);
      applyFilters();
    } catch (err) {
      window.OneSpaceUtils.showError(err.message || "Failed to load tasks");
    }
  }

  function applyFilters() {
    const statusVal = statusFilter.value;
    const priorityVal = priorityFilter.value;
    const searchVal = searchInput.value.trim().toLowerCase();

    let filtered = allTasks;
    if (statusVal) filtered = filtered.filter(function (t) { return t.status === statusVal; });
    if (priorityVal) filtered = filtered.filter(function (t) { return t.priority === priorityVal; });
    if (searchVal) {
      filtered = filtered.filter(function (t) {
        return t.title.toLowerCase().includes(searchVal) ||
               (t.description || "").toLowerCase().includes(searchVal) ||
               t.status.toLowerCase().includes(searchVal) ||
               t.priority.toLowerCase().includes(searchVal);
      });
    }
    renderTasks(filtered);
  }

  function renderTasks(tasks) {
    if (!tasks.length) {
      tasksBody.innerHTML = "";
      tasksCard.querySelector("table").classList.add("d-none");
      tasksEmpty.classList.remove("d-none");
      tasksEmpty.classList.remove("hidden");
      return;
    }
    tasksCard.querySelector("table").classList.remove("d-none");
    tasksEmpty.classList.add("d-none");
    tasksBody.innerHTML = tasks.map(function (t) {
      const badgeClass = t.status === "Done" ? "bg-success" : t.status === "In Progress" ? "bg-primary" : "bg-secondary";
      const priorityClass = t.priority === "High" ? "text-danger" : t.priority === "Medium" ? "text-warning" : "text-info";
      const due = t.due_date ? window.OneSpaceUtils.formatDate(t.due_date) : "—";
      const overdue = t.due_date && t.status !== "Done" && new Date(t.due_date + "T23:59:59") < new Date();
      return `
        <tr data-id="${t.id}" class="hover:bg-surface-container-low/50 transition-colors">
          <td class="px-md py-sm">
            <strong>${window.OneSpaceUtils.escapeHtml(t.title)}</strong>
            ${t.description ? `<div class="text-muted small">${window.OneSpaceUtils.escapeHtml(t.description).substring(0, 100)}${t.description.length > 100 ? "…" : ""}</div>` : ""}
          </td>
          <td class="px-md py-sm">
            <select class="form-select form-select-sm status-select" data-id="${t.id}" aria-label="Change status">
              <option value="To Do" ${t.status === "To Do" ? "selected" : ""}>To Do</option>
              <option value="In Progress" ${t.status === "In Progress" ? "selected" : ""}>In Progress</option>
              <option value="Done" ${t.status === "Done" ? "selected" : ""}>Done</option>
            </select>
          </td>
          <td class="px-md py-sm hidden sm:table-cell"><span class="badge bg-light ${priorityClass}">${window.OneSpaceUtils.escapeHtml(t.priority)}</span></td>
          <td class="px-md py-sm hidden md:table-cell ${overdue ? "text-danger fw-bold" : ""}">${due}${overdue ? ' <i class="bi bi-exclamation-triangle-fill" title="Overdue"></i>' : ""}</td>
          <td class="px-md py-sm text-end">
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-secondary edit-btn" data-id="${t.id}" aria-label="Edit task">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-outline-danger delete-btn" data-id="${t.id}" aria-label="Delete task">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");

    // Attach event listeners for status change
    tasksBody.querySelectorAll(".status-select").forEach(function (select) {
      select.addEventListener("change", async function () {
        const taskId = this.dataset.id;
        const newStatus = this.value;
        const task = allTasks.find(function (t) { return t.id === taskId; });
        if (task && task.status !== newStatus) {
          try {
            await window.OneSpaceAPI.updateTask(workspaceId, taskId, { status: newStatus });
            window.OneSpaceUtils.showSuccess("Task status updated");
            loadTasks();
          } catch (err) {
            window.OneSpaceUtils.showError(err.message);
            loadTasks(); // revert
          }
        }
      });
    });

    // Edit buttons
    tasksBody.querySelectorAll(".edit-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openEditModal(this.dataset.id);
      });
    });

    // Delete buttons
    tasksBody.querySelectorAll(".delete-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        deleteTask(this.dataset.id);
      });
    });
  }

  function openAddModal() {
    taskForm.reset();
    taskForm.classList.remove("was-validated");
    taskIdInput.value = "";
    modalLabel.textContent = "Add Task";
    taskStatusInput.value = "To Do";
    taskPriorityInput.value = "Medium";
    taskDueDateInput.value = "";
    taskModal.show();
  }

  function openEditModal(taskId) {
    const task = allTasks.find(function (t) { return t.id === taskId; });
    if (!task) return;
    taskForm.reset();
    taskForm.classList.remove("was-validated");
    taskIdInput.value = task.id;
    taskTitleInput.value = task.title;
    taskDescriptionInput.value = task.description || "";
    taskStatusInput.value = task.status;
    taskPriorityInput.value = task.priority;
    taskDueDateInput.value = task.due_date || "";
    modalLabel.textContent = "Edit Task";
    taskModal.show();
  }

  taskForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    event.stopPropagation();

    if (!taskForm.checkValidity()) {
      taskForm.classList.add("was-validated");
      return;
    }

    setSubmitLoading(true);
    const data = {
      title: taskTitleInput.value.trim(),
      description: taskDescriptionInput.value.trim(),
      status: taskStatusInput.value,
      priority: taskPriorityInput.value,
      due_date: taskDueDateInput.value || null
    };

    try {
      if (taskIdInput.value) {
        await window.OneSpaceAPI.updateTask(workspaceId, taskIdInput.value, data);
        window.OneSpaceUtils.showSuccess("Task updated");
      } else {
        await window.OneSpaceAPI.createTask(workspaceId, data);
        window.OneSpaceUtils.showSuccess("Task created");
      }
      taskModal.hide();
      loadTasks();
    } catch (err) {
      window.OneSpaceUtils.showError(err.message);
    } finally {
      setSubmitLoading(false);
    }
  });

  async function deleteTask(taskId) {
    if (!confirm("Delete this task? This cannot be undone.")) return;
    try {
      await window.OneSpaceAPI.deleteTask(workspaceId, taskId);
      window.OneSpaceUtils.showSuccess("Task deleted");
      loadTasks();
    } catch (err) {
      window.OneSpaceUtils.showError(err.message);
    }
  }

  function setSubmitLoading(isLoading) {
    taskSubmit.disabled = isLoading;
    taskBtnText.classList.toggle("d-none", isLoading);
    taskBtnLoading.classList.toggle("d-none", !isLoading);
  }

  // Event listeners
  addTaskBtn.addEventListener("click", openAddModal);
  emptyAddTaskBtn.addEventListener("click", openAddModal);
  statusFilter.addEventListener("change", applyFilters);
  priorityFilter.addEventListener("change", applyFilters);
  searchInput.addEventListener("input", window.OneSpaceUtils.debounce(applyFilters, 300));
  clearSearch.addEventListener("click", function () {
    searchInput.value = "";
    applyFilters();
  });

  taskModalEl.addEventListener("hidden.bs.modal", function () {
    taskForm.reset();
    taskForm.classList.remove("was-validated");
  });

  // Initial load
  loadTasks();
});