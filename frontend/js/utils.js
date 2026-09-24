window.OneSpaceUtils = window.OneSpaceUtils || {};

window.OneSpaceUtils.getQueryParam = function (name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
};

window.OneSpaceUtils.formatDate = function (value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
};

window.OneSpaceUtils.formatDateTime = function (value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

window.OneSpaceUtils.formatRelativeTime = function (value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) {
    return "just now";
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return minutes === 1 ? "1 minute ago" : `${minutes} minutes ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  }
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return days === 1 ? "1 day ago" : `${days} days ago`;
  }
  return window.OneSpaceUtils.formatDate(value);
};

window.OneSpaceUtils.showToast = function (message, type = "success") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toastElement = document.createElement("div");
  const backgroundClass = type === "danger" ? "text-bg-danger" : type === "warning" ? "text-bg-warning" : "text-bg-success";

  toastElement.className = `toast align-items-center border-0 ${backgroundClass}`;
  toastElement.setAttribute("role", "status");
  toastElement.setAttribute("aria-live", "polite");

  const body = document.createElement("div");
  body.className = "toast-body";
  body.textContent = message;

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "btn-close btn-close-white me-2 m-auto";
  closeButton.setAttribute("aria-label", "Dismiss notification");
  closeButton.addEventListener("click", function () {
    const toast = bootstrap.Toast.getOrCreateInstance(toastElement);
    toast.hide();
  });

  toastElement.appendChild(body);
  toastElement.appendChild(closeButton);
  container.appendChild(toastElement);

  if (window.bootstrap && bootstrap.Toast) {
    const toast = bootstrap.Toast.getOrCreateInstance(toastElement, { delay: 3500 });
    toast.show();
    toastElement.addEventListener("hidden.bs.toast", function () {
      toastElement.remove();
    });
  } else {
    window.setTimeout(function () {
      toastElement.remove();
    }, 3500);
  }
};

window.OneSpaceUtils.showError = function (message) {
  window.OneSpaceUtils.showToast(message, "danger");
};

window.OneSpaceUtils.showSuccess = function (message) {
  window.OneSpaceUtils.showToast(message, "success");
};

window.OneSpaceUtils.debounce = function (callback, wait = 300) {
  let timeoutId;
  return function debounced(...args) {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(function () {
      callback.apply(this, args);
    }, wait);
  };
};

window.OneSpaceUtils.escapeHtml = function (value) {
  const text = value === null || value === undefined ? "" : String(value);
  const escapeMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, function (character) {
    return escapeMap[character];
  });
};

window.OneSpaceUtils.formatFileSize = function (bytes) {
  const num = Number(bytes);
  if (!Number.isFinite(num) || num <= 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(num) / Math.log(k)), sizes.length - 1);
  return parseFloat((num / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  container.className = "toast-container position-fixed top-0 end-0 p-3";
  container.style.zIndex = "1090";
  document.body.appendChild(container);
  return container;
}
