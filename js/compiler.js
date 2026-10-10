document.addEventListener("DOMContentLoaded", async function () {
  if (!window.OneSpaceAuth.requireAuth()) return;

  const workspaceId = window.OneSpaceUtils.getQueryParam("workspace_id");
  if (!workspaceId) {
    window.location.replace("workspaces.html");
    return;
  }

  // Update all navigation links with workspace_id (same as other workspace pages)
  document.querySelectorAll("[data-nav]").forEach(function (link) {
    const page = link.getAttribute("data-nav");
    link.href = `${page}.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  });
  document.getElementById("dashboardLink").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;
  document.getElementById("backDashboard").href = `dashboard.html?workspace_id=${encodeURIComponent(workspaceId)}`;

  // ------------------------------------------------------------------
  // Element refs
  // ------------------------------------------------------------------
  const languageSelect = document.getElementById("languageSelect");
  const codeEditor = document.getElementById("codeEditor");
  const outputPanel = document.getElementById("outputPanel");
  const runButton = document.getElementById("runBtn");
  const runButtonText = runButton.querySelector(".btn-text");
  const runButtonLoading = runButton.querySelector(".btn-loading");
  const clearButton = document.getElementById("clearBtn");
  const runStatus = document.getElementById("runStatus");

  const savedSelect = document.getElementById("savedSelect");
  const saveSnippetBtn = document.getElementById("saveSnippetBtn");
  const renameSnippetBtn = document.getElementById("renameSnippetBtn");
  const deleteSnippetBtn = document.getElementById("deleteSnippetBtn");

  const saveSnippetModalEl = document.getElementById("saveSnippetModal");
  const saveSnippetModal = new bootstrap.Modal(saveSnippetModalEl);
  const saveSnippetForm = document.getElementById("saveSnippetForm");
  const snippetTitleInput = document.getElementById("snippetTitle");
  const saveSnippetModalLabel = document.getElementById("saveSnippetModalLabel");
  const saveSnippetSubmit = document.getElementById("saveSnippetSubmit");
  const saveSnippetBtnText = saveSnippetSubmit.querySelector(".btn-text");
  const saveSnippetBtnLoading = saveSnippetSubmit.querySelector(".btn-loading");

  const exitModalEl = document.getElementById("exitModal");
  const exitModal = new bootstrap.Modal(exitModalEl, { backdrop: "static" });
  const exitSaveBtn = document.getElementById("exitSaveBtn");
  const exitSaveBtnText = exitSaveBtn.querySelector(".btn-text");
  const exitSaveBtnLoading = exitSaveBtn.querySelector(".btn-loading");
  const exitDiscardBtn = document.getElementById("exitDiscardBtn");
  const exitCancelBtn = document.getElementById("exitCancelBtn");
  const exitCloseBtn = exitModalEl.querySelector(".btn-close");

  // ------------------------------------------------------------------
  // LANGUAGES registry
  // The <select> options, starter programs, and Run behaviour are all
  // generated from this object. To support a new language, add one entry:
  //   { label, starter, run(code) => Promise<string> }
  // ------------------------------------------------------------------
  const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
  const PYODIDE_SCRIPT_SRC = PYODIDE_INDEX_URL + "pyodide.js";

  const LANGUAGES = {
    python: {
      label: "Python",
      starter: '# Welcome to the OneSpace compiler.\nprint("Hello, OneSpace!")\n\n# Uncomment the line below to see a syntax error:\n# print(\n',
      run: runPython
    }
  };

  // Cached Pyodide runtime, created lazily on the first Run click.
  let pyodideRuntime = null;
  let pyodideLoading = null;

  // Set when a Python program raises an error, so the UI can show a useful
  // status instead of "Done" for a program that actually failed.
  let lastRunFailed = false;

  async function runPython(code) {
    const pyodide = await ensurePyodide();

    runStatus.textContent = "Running...";
    lastRunFailed = false;

    let output = "";
    function collect(text) {
      output += text + "\n";
    }

    pyodide.setStdout({ batched: collect });
    pyodide.setStderr({ batched: collect });

    try {
      await pyodide.runPythonAsync(code);
    } catch (error) {
      // Python errors (including syntax errors) surface as a thrown error
      // whose message contains the traceback.
      lastRunFailed = true;
      const message = String((error && error.message) || error);
      if (message && !output.includes(message)) {
        output += message + "\n";
      }
    } finally {
      // Stop forwarding Python output to the console after the run ends.
      pyodide.setStdout({ batched: function () { } });
      pyodide.setStderr({ batched: function () { } });
    }

    return output.replace(/\n+$/, "");
  }

  async function ensurePyodide() {
    if (pyodideRuntime) return pyodideRuntime;
    if (pyodideLoading) return pyodideLoading;

    runStatus.textContent = "Loading Python runtime (first run only)...";

    pyodideLoading = (async function () {
      if (typeof window.loadPyodide !== "function") {
        await loadScript(PYODIDE_SCRIPT_SRC);
      }
      pyodideRuntime = await window.loadPyodide({ indexURL: PYODIDE_INDEX_URL });
      return pyodideRuntime;
    })().catch(function (error) {
      pyodideLoading = null; // allow a retry on the next Run click
      throw error;
    });

    return pyodideLoading;
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error("The Python runtime could not be loaded from the CDN. Check your connection and try again."));
      };
      document.head.appendChild(script);
    });
  }

  // ------------------------------------------------------------------
  // Saved programs ("snippets")
  // ------------------------------------------------------------------
  let allSnippets = [];
  let currentSnippet = null; // snippet loaded in the editor, or null if unsaved
  let lastSavedCode = null;  // editor contents at the last clean point

  let snippetModalMode = "create"; // "create" | "rename" | "saveAndExit"

  let pendingExitAction = null; // runs after the user resolves the exit prompt
  let exitActionTaken = false;  // true once we are actually leaving
  let exitSaveChain = false;    // true while the name modal is open mid-exit
  let snippetSaveInProgress = false;

  function isDirty() {
    return codeEditor.value !== lastSavedCode;
  }

  function markClean(code, snippet) {
    lastSavedCode = code;
    currentSnippet = snippet || null;
  }

  function updateSnippetActions() {
    const hasSnippet = Boolean(currentSnippet);
    renameSnippetBtn.disabled = !hasSnippet;
    deleteSnippetBtn.disabled = !hasSnippet;
  }

  function languageLabel(languageKey) {
    return LANGUAGES[languageKey] ? LANGUAGES[languageKey].label : languageKey;
  }

  function renderSavedSelect() {
    // Rebuild options with DOM APIs so user-entered titles can never inject markup.
    savedSelect.textContent = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Saved programs…";
    savedSelect.appendChild(placeholder);

    allSnippets
      .slice()
      .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)))
      .forEach(function (snippet) {
        const option = document.createElement("option");
        option.value = snippet.id;
        option.textContent = `${snippet.title} (${languageLabel(snippet.language)})`;
        savedSelect.appendChild(option);
      });

    savedSelect.value = currentSnippet ? currentSnippet.id : "";
  }

  async function loadSnippets() {
    try {
      allSnippets = await window.OneSpaceAPI.getSnippets(workspaceId);
      renderSavedSelect();
    } catch (error) {
      window.OneSpaceUtils.showError(error.message || "Failed to load saved programs.");
    }
  }

  function selectSnippet(id) {
    if (!id) return;
    const snippet = allSnippets.find(function (s) {
      return s.id === id;
    });
    if (!snippet) return;

    if (LANGUAGES[snippet.language]) {
      languageSelect.value = snippet.language;
    } else {
      languageSelect.value = Object.keys(LANGUAGES)[0];
    }
    codeEditor.value = snippet.code;
    clearOutput();
    markClean(snippet.code, snippet);
    savedSelect.value = snippet.id;
    updateSnippetActions();
  }

  // Toolbar Save: updates the loaded program, or opens the name modal for a new one.
  saveSnippetBtn.addEventListener("click", function () {
    if (currentSnippet) {
      saveInPlace();
    } else {
      openNameModal("create", "");
    }
  });

  async function saveInPlace() {
    if (snippetSaveInProgress) return;
    snippetSaveInProgress = true;
    saveSnippetBtn.disabled = true;
    try {
      const updated = await window.OneSpaceAPI.updateSnippet(workspaceId, currentSnippet.id, {
        title: currentSnippet.title,
        language: languageSelect.value,
        code: codeEditor.value
      });
      currentSnippet = updated;
      markClean(codeEditor.value, updated);
      await loadSnippets();
      window.OneSpaceUtils.showSuccess("Program saved.");
    } catch (error) {
      window.OneSpaceUtils.showError(error.message || "Failed to save program.");
    } finally {
      snippetSaveInProgress = false;
      saveSnippetBtn.disabled = false;
      updateSnippetActions();
    }
  }

  renameSnippetBtn.addEventListener("click", function () {
    if (!currentSnippet) return;
    openNameModal("rename", currentSnippet.title);
  });

  deleteSnippetBtn.addEventListener("click", async function () {
    if (!currentSnippet) return;
    if (!window.confirm(`Delete "${currentSnippet.title}"? This cannot be undone.`)) return;
    try {
      await window.OneSpaceAPI.deleteSnippet(workspaceId, currentSnippet.id);
      window.OneSpaceUtils.showSuccess("Program deleted.");
      // The editor keeps its text; treat it as a new, unsaved program.
      lastSavedCode = codeEditor.value;
      currentSnippet = null;
      await loadSnippets();
      updateSnippetActions();
    } catch (error) {
      window.OneSpaceUtils.showError(error.message || "Failed to delete program.");
    }
  });

  function openNameModal(mode, prefill) {
    snippetModalMode = mode;
    snippetTitleInput.value = prefill || "";
    saveSnippetModalLabel.textContent = mode === "rename" ? "Rename Program" : "Save Program";
    saveSnippetForm.classList.remove("was-validated");
    saveSnippetModal.show();
  }

  function setSaveModalLoading(isLoading) {
    saveSnippetSubmit.disabled = isLoading;
    saveSnippetBtnText.classList.toggle("d-none", isLoading);
    saveSnippetBtnLoading.classList.toggle("d-none", !isLoading);
  }

  saveSnippetForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    event.stopPropagation();
    if (!saveSnippetForm.checkValidity()) {
      saveSnippetForm.classList.add("was-validated");
      return;
    }

    const title = snippetTitleInput.value.trim() || "Untitled program";
    setSaveModalLoading(true);
    try {
      if (snippetModalMode === "rename" && currentSnippet) {
        const updated = await window.OneSpaceAPI.updateSnippet(workspaceId, currentSnippet.id, { title });
        currentSnippet = updated;
        window.OneSpaceUtils.showSuccess("Program renamed.");
      } else {
        const code = codeEditor.value;
        const language = languageSelect.value;
        if (currentSnippet) {
          const updated = await window.OneSpaceAPI.updateSnippet(workspaceId, currentSnippet.id, { title, language, code });
          currentSnippet = updated;
        } else {
          const created = await window.OneSpaceAPI.createSnippet(workspaceId, { title, language, code });
          currentSnippet = created;
        }
        markClean(codeEditor.value, currentSnippet);
        window.OneSpaceUtils.showSuccess("Program saved.");
      }

      const wasSaveAndExit = snippetModalMode === "saveAndExit";
      snippetModalMode = "create";
      saveSnippetModal.hide();
      await loadSnippets();
      updateSnippetActions();
      if (wasSaveAndExit) {
        takeExitAction();
      }
    } catch (error) {
      window.OneSpaceUtils.showError(error.message || "Failed to save program.");
    } finally {
      setSaveModalLoading(false);
    }
  });

  // If the Save/Rename modal is dismissed mid save-and-exit, abort the exit.
  saveSnippetModalEl.addEventListener("hidden.bs.modal", function () {
    if (snippetModalMode === "saveAndExit" && !exitActionTaken) {
      snippetModalMode = "create";
      pendingExitAction = null;
      exitSaveChain = false;
    } else if (snippetModalMode !== "create") {
      snippetModalMode = "create";
    }
  });

  savedSelect.addEventListener("change", function () {
    const selectedId = savedSelect.value;
    if (!selectedId) return;
    if (isDirty()) {
      // Never discard unsaved edits silently.
      requestExit(function () {
        selectSnippet(selectedId);
      });
    } else {
      selectSnippet(selectedId);
    }
  });

  // ------------------------------------------------------------------
  // Exit prompt (save before leaving)
  // ------------------------------------------------------------------
  function requestExit(action) {
    if (!isDirty()) {
      action();
      return;
    }
    pendingExitAction = action;
    exitActionTaken = false;
    exitSaveChain = false;
    exitModal.show();
  }

  function takeExitAction() {
    exitActionTaken = true;
    const action = pendingExitAction;
    pendingExitAction = null;
    lastSavedCode = codeEditor.value; // mark clean before leaving
    if (action) action();
  }

  function cancelExit() {
    pendingExitAction = null;
    exitSaveChain = false;
    exitModal.hide();
  }

  exitSaveBtn.addEventListener("click", async function () {
    setExitSaveLoading(true);
    try {
      if (currentSnippet) {
        const updated = await window.OneSpaceAPI.updateSnippet(workspaceId, currentSnippet.id, {
          title: currentSnippet.title,
          language: languageSelect.value,
          code: codeEditor.value
        });
        currentSnippet = updated;
        markClean(codeEditor.value, updated);
        await loadSnippets();
        setExitSaveLoading(false);
        exitModal.hide();
        takeExitAction();
      } else {
        // No program loaded yet — ask for a name, then navigate.
        exitSaveChain = true;
        exitModal.hide();
        setExitSaveLoading(false);
        openNameModal("saveAndExit", "");
      }
    } catch (error) {
      setExitSaveLoading(false);
      window.OneSpaceUtils.showError(error.message || "Failed to save program.");
    }
  });

  function setExitSaveLoading(isLoading) {
    exitSaveBtn.disabled = isLoading;
    exitSaveBtnText.classList.toggle("d-none", isLoading);
    exitSaveBtnLoading.classList.toggle("d-none", !isLoading);
  }

  exitDiscardBtn.addEventListener("click", function () {
    exitModal.hide();
    takeExitAction();
  });

  exitCancelBtn.addEventListener("click", cancelExit);
  exitCloseBtn.addEventListener("click", cancelExit);

  // Closing the exit modal some other way (Esc, backdrop) cancels the exit.
  exitModalEl.addEventListener("hidden.bs.modal", function () {
    if (!exitActionTaken && !exitSaveChain && pendingExitAction) {
      pendingExitAction = null;
    }
  });

  // Intercept in-app navigation while the editor is dirty. Runs in the capture
  // phase so it fires before the injected sidebar's own handlers.
  function isInAppHref(href) {
    if (!href) return false;
    return !/^(https?:|mailto:|tel:|#|javascript:)/i.test(href);
  }

  function logoutAction() {
    Promise.resolve(window.OneSpaceAuth.logout ? window.OneSpaceAuth.logout() : undefined).then(function () {
      window.location.replace("login.html");
    });
  }

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    const anchor = target.closest("a[href]");
    if (anchor && isInAppHref(anchor.getAttribute("href"))) {
      if (isDirty()) {
        event.preventDefault();
        event.stopPropagation();
        const href = anchor.getAttribute("href");
        requestExit(function () {
          window.location.href = href;
        });
      }
      return;
    }

    const logoutButton = target.closest("#logoutBtn, #logoutBtnMobile");
    if (logoutButton) {
      if (isDirty()) {
        event.preventDefault();
        event.stopPropagation();
        requestExit(logoutAction);
      }
      // When clean, the injected sidebar handles logout itself.
    }
  }, true);

  // Fallback for tab close / refresh / browser back (only a generic message is
  // possible there; in-app navigation is handled by the styled exit modal).
  window.addEventListener("beforeunload", function (event) {
    if (isDirty()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  // ------------------------------------------------------------------
  // UI wiring
  // ------------------------------------------------------------------

  // Populate the language <select> from the LANGUAGES registry.
  Object.keys(LANGUAGES).forEach(function (key) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = LANGUAGES[key].label;
    languageSelect.appendChild(option);
  });

  function loadStarter() {
    const language = LANGUAGES[languageSelect.value];
    if (language) {
      codeEditor.value = language.starter;
    }
  }

  function setRunning(isRunning) {
    runButton.disabled = isRunning;
    runButtonText.classList.toggle("d-none", isRunning);
    runButtonLoading.classList.toggle("d-none", !isRunning);
  }

  function clearOutput() {
    outputPanel.textContent = "";
    runStatus.textContent = "";
    lastRunFailed = false;
  }

  async function handleRun() {
    const language = LANGUAGES[languageSelect.value];
    if (!language) return;

    outputPanel.textContent = "";
    lastRunFailed = false;
    setRunning(true);
    runStatus.textContent = "Running...";

    try {
      const result = await language.run(codeEditor.value);
      outputPanel.textContent = result;
      runStatus.textContent = lastRunFailed ? "Python error" : "Done";
    } catch (error) {
      // Runtime load failure or an unexpected engine error.
      const message = String((error && error.message) || error);
      outputPanel.textContent = "Failed to run code: " + message;
      runStatus.textContent = "Error";
    } finally {
      setRunning(false);
    }
  }

  runButton.addEventListener("click", handleRun);
  clearButton.addEventListener("click", clearOutput);

  languageSelect.addEventListener("change", function () {
    const newValue = languageSelect.value;
    const apply = function () {
      languageSelect.value = newValue;
      loadStarter();
      clearOutput();
      markClean(codeEditor.value, null);
      updateSnippetActions();
    };
    if (isDirty()) {
      // Changing language replaces the editor contents — never discard silently.
      requestExit(apply);
    } else {
      apply();
    }
  });

  codeEditor.addEventListener("keydown", function (event) {
    // Ctrl/Cmd + Enter runs the current program.
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      handleRun();
    }
  });

  // Initial state
  loadStarter();
  markClean(codeEditor.value, null);
  updateSnippetActions();
  loadSnippets();
});