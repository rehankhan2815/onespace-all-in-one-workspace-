document.addEventListener("DOMContentLoaded", function () {
  if (window.OneSpaceAuth && window.OneSpaceAuth.isAuthenticated()) {
    window.location.replace("workspaces.html");
    return;
  }

  const form = document.getElementById("registerForm");
  const passwordInput = document.getElementById("password");
  const confirmInput = document.getElementById("confirmPassword");
  const toggleBtn = document.getElementById("togglePassword");
  const toggleIcon = toggleBtn.querySelector("i");
  const registerBtn = document.getElementById("registerBtn");
  const btnText = registerBtn.querySelector(".btn-text");
  const btnLoading = registerBtn.querySelector(".btn-loading");
  const errorAlert = document.getElementById("registerError");
  const successAlert = document.getElementById("registerSuccess");

  toggleBtn.addEventListener("click", function () {
    const type = passwordInput.type === "password" ? "text" : "password";
    passwordInput.type = type;
    confirmInput.type = type;
    toggleIcon.textContent = type === "password" ? "visibility_off" : "visibility";
    toggleBtn.setAttribute("aria-label", type === "password" ? "Show passwords" : "Hide passwords");
  });

  function validatePasswordMatch() {
    if (confirmInput.value && passwordInput.value !== confirmInput.value) {
      confirmInput.setCustomValidity("Passwords do not match.");
    } else {
      confirmInput.setCustomValidity("");
    }
  }

  passwordInput.addEventListener("input", validatePasswordMatch);
  confirmInput.addEventListener("input", validatePasswordMatch);

  if (window.OneSpaceMockData) {
    window.OneSpaceMockData.seed();
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    event.stopPropagation();

    validatePasswordMatch();

    if (!form.checkValidity()) {
      form.classList.add("was-validated");
      return;
    }

    setLoading(true);
    hideMessages();

    try {
      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim().toLowerCase();
      await window.OneSpaceAuth.register({
        name: name,
        email: email,
        password: passwordInput.value,
        confirmPassword: confirmInput.value
      });

      showSuccess("Account created successfully! Redirecting to login…");
      window.setTimeout(function () {
        window.location.replace("login.html");
      }, 1200);
    } catch (err) {
      showError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    registerBtn.disabled = isLoading;
    btnText.classList.toggle("d-none", isLoading);
    btnLoading.classList.toggle("d-none", !isLoading);
    if (isLoading) btnLoading.classList.remove("hidden");
  }

  function showError(message) {
    errorAlert.textContent = message;
    errorAlert.classList.remove("d-none");
    errorAlert.classList.remove("hidden");
    successAlert.classList.add("d-none");
  }

  function showSuccess(message) {
    successAlert.textContent = message;
    successAlert.classList.remove("d-none");
    successAlert.classList.remove("hidden");
    errorAlert.classList.add("d-none");
  }

  function hideMessages() {
    errorAlert.classList.add("d-none");
    successAlert.classList.add("d-none");
    errorAlert.textContent = "";
    successAlert.textContent = "";
  }
});