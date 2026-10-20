(function () {
  var NAV_ITEMS = [
    { page: "workspaces", icon: "home", label: "Workspaces" },
    { page: "dashboard", icon: "dashboard", label: "Dashboard" },
    { page: "tasks", icon: "checklist", label: "Tasks" },
    { page: "notes", icon: "description", label: "Notes" },
    { page: "resources", icon: "menu_book", label: "Resources" },
    { page: "files", icon: "folder", label: "Files" },
    { page: "search", icon: "search", label: "Search" },
    { page: "compiler", icon: "code", label: "Compiler" }
  ];

  function getCurrentPage() {
    var path = window.location.pathname.split("/").pop();
    var file = path.split("?")[0];
    var match = file.match(/^(workspaces|dashboard|tasks|notes|resources|files|search|compiler)\.html$/);
    return match ? match[1] : null;
  }

  function getWorkspaceId() {
    if (window.OneSpaceUtils && window.OneSpaceUtils.getQueryParam) {
      return window.OneSpaceUtils.getQueryParam("workspace_id");
    }
    return new URLSearchParams(window.location.search).get("workspace_id");
  }

  function hrefFor(page, workspaceId) {
    if (page === "workspaces") return "workspaces.html";
    return workspaceId
      ? page + ".html?workspace_id=" + encodeURIComponent(workspaceId)
      : page + ".html";
  }

  function inject() {
    var current = getCurrentPage();
    if (!current) return;

    var workspaceId = getWorkspaceId();

    var activeCls = "flex items-center gap-md px-md py-sm bg-secondary-container text-on-secondary-container border-l-4 border-primary opacity-90 transition-all font-bold";
    var inactiveCls = "flex items-center gap-md px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-colors duration-200 border-l-4 border-transparent";

    var filler = function (icon) {
      return '<span class="material-symbols-outlined" style="font-variation-settings: \'FILL\' 1;">' + icon + '</span>';
    };
    var plainIcon = function (icon) {
      return '<span class="material-symbols-outlined">' + icon + '</span>';
    };

    var desktopLinks = NAV_ITEMS.map(function (item) {
      var isActive = item.page === current;
      return '<a class="' + (isActive ? activeCls : inactiveCls) + '" href="' + hrefFor(item.page, workspaceId) + '" data-nav="' + item.page + '">' +
        (isActive ? filler(item.icon) : plainIcon(item.icon)) + ' ' + item.label + '</a>';
    }).join("\n    ");

    var newProjectBtn = current === "workspaces"
      ? '<button class="w-full bg-primary text-on-primary h-11 rounded-lg font-label-sm text-label-sm flex items-center justify-center gap-sm hover:bg-primary-fixed-variant transition-colors" type="button" data-bs-toggle="modal" data-bs-target="#createWorkspaceModal">' +
        '<span class="material-symbols-outlined text-lg">add</span> New Project</button>'
      : '<a href="workspaces.html" class="w-full bg-primary text-on-primary h-11 rounded-lg font-label-sm text-label-sm flex items-center justify-center gap-sm hover:bg-primary-fixed-variant transition-colors">' +
        '<span class="material-symbols-outlined text-lg">add</span> New Project</a>';

    var sidebar =
      '<!-- Injected SideNavBar -->\n' +
      '<nav class="fixed left-0 top-0 h-screen hidden md:flex flex-col z-40 bg-surface dark:bg-surface-container-low border-r border-outline-variant dark:border-outline w-[280px]">\n' +
      '  <div class="p-lg flex items-center gap-md">\n' +
      '    <div class="w-10 h-10 rounded-lg bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-lg">O</div>\n' +
      '    <div>\n' +
      '      <div class="font-display-lg text-display-lg font-bold text-primary dark:text-inverse-primary text-xl">OneSpace</div>\n' +
      '      <div class="font-label-sm text-label-sm text-on-surface-variant">Academic Workspace</div>\n' +
      '    </div>\n' +
      '  </div>\n' +
      '  <div class="px-md pb-md">\n' +
      '    ' + newProjectBtn + '\n' +
      '  </div>\n' +
      '  <div class="flex-1 overflow-y-auto py-sm flex flex-col gap-xs font-body-md text-body-md">\n' +
      '    ' + desktopLinks + '\n' +
      '  </div>\n' +
      '  <div class="mt-auto py-md border-t border-outline-variant flex flex-col gap-xs font-body-md text-body-md">\n' +
      '    <button class="flex items-center gap-md px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-colors duration-200 border-l-4 border-transparent text-left w-full" id="logoutBtn" type="button">\n' +
      '      <span class="material-symbols-outlined">logout</span> Logout\n' +
      '    </button>\n' +
      '  </div>\n' +
      '</nav>\n\n';

    var mobileTop =
      '<!-- Injected Mobile TopAppBar -->\n' +
      '<header class="md:hidden flex justify-between items-center w-full px-lg sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-outline-variant h-16">\n' +
      '  <div class="font-headline-sm text-headline-sm font-bold text-primary dark:text-inverse-primary">OneSpace</div>\n' +
      '  <button class="text-on-surface-variant hover:bg-surface-container-high rounded-full p-2 transition-all" type="button" id="logoutBtnMobile">\n' +
      '    <span class="material-symbols-outlined">logout</span>\n' +
      '  </button>\n' +
      '</header>\n\n';

    var bottomLinks = NAV_ITEMS.map(function (item) {
      var isActive = item.page === current;
      var cls = isActive
        ? "flex flex-col items-center justify-center bg-primary-container text-on-primary-container rounded-xl p-2 scale-90 transition-transform font-bold"
        : "flex flex-col items-center justify-center text-on-surface-variant p-2 hover:bg-surface-container-high rounded-xl transition-all";
      return '<a class="' + cls + '" href="' + hrefFor(item.page, workspaceId) + '" data-nav="' + item.page + '">' +
        (isActive ? filler(item.icon) : plainIcon(item.icon)) +
        '<span class="font-label-sm text-label-sm mt-1 text-[9px] leading-none whitespace-nowrap">' + item.label + '</span></a>';
    }).join("\n  ");

    var bottomNav =
      '<!-- Injected Mobile BottomNavBar -->\n' +
      '<nav class="fixed bottom-0 left-0 w-full z-50 flex items-center justify-around md:hidden bg-surface dark:bg-inverse-surface border-t border-outline-variant shadow-lg px-1 py-2 gap-1">\n' +
      '  ' + bottomLinks + '\n' +
      '</nav>\n';

    document.body.insertAdjacentHTML("afterbegin", sidebar + mobileTop);
    document.body.insertAdjacentHTML("beforeend", bottomNav);

    function doLogout() {
      var logoutPromise = window.OneSpaceAuth && window.OneSpaceAuth.logout
        ? window.OneSpaceAuth.logout()
        : Promise.resolve();
      Promise.resolve(logoutPromise).then(function () {
        window.location.replace("login.html");
      });
    }

    ["logoutBtn", "logoutBtnMobile"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("click", doLogout);
    });
  }

  if (document.body) {
    inject();
  } else {
    document.addEventListener("DOMContentLoaded", inject);
  }
})();