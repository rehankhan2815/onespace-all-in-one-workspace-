window.OneSpaceMockData = {
  users: [
    {
      id: "user-demo",
      name: "Demo User",
      email: "demo@onespace.test",
      password: "demo123"
    },
    {
      id: "user-alex",
      name: "Alex Morgan",
      email: "alex@onespace.test",
      password: "alex123"
    }
  ],
  workspaces: [
    {
      id: "ws-design",
      name: "Product Design System",
      description: "Shared research, UI decisions, and component planning for the next product release.",
      created_at: "2026-07-12T09:00:00.000Z",
      updated_at: "2026-09-08T14:20:00.000Z",
      archived: false
    },
    {
      id: "ws-research",
      name: "Market Research",
      description: "Customer interviews, competitor notes, and opportunity tracking.",
      created_at: "2026-06-03T11:30:00.000Z",
      updated_at: "2026-09-05T10:15:00.000Z",
      archived: false
    },
    {
      id: "ws-community",
      name: "Community Events",
      description: "Planning and resources for campus workshops and meetup programs.",
      created_at: "2026-05-18T08:45:00.000Z",
      updated_at: "2026-08-21T16:40:00.000Z",
      archived: true
    }
  ],
  tasks: [
    {
      id: "task-1",
      workspace_id: "ws-design",
      title: "Audit component accessibility",
      description: "Review keyboard navigation, focus states, and screen reader labels across the core components.",
      status: "In Progress",
      priority: "High",
      due_date: "2026-09-18",
      created_at: "2026-09-01T09:00:00.000Z",
      updated_at: "2026-09-08T13:10:00.000Z"
    },
    {
      id: "task-2",
      workspace_id: "ws-design",
      title: "Prepare design handoff checklist",
      description: "Document tokens, responsive behavior, and interaction states for engineering.",
      status: "To Do",
      priority: "Medium",
      due_date: "2026-09-22",
      created_at: "2026-09-03T10:20:00.000Z",
      updated_at: "2026-09-03T10:20:00.000Z"
    },
    {
      id: "task-3",
      workspace_id: "ws-design",
      title: "Publish color token updates",
      description: "Update the token library and share the migration notes with the product team.",
      status: "Done",
      priority: "Medium",
      due_date: "2026-09-06",
      created_at: "2026-08-28T12:00:00.000Z",
      updated_at: "2026-09-06T15:35:00.000Z"
    },
    {
      id: "task-4",
      workspace_id: "ws-research",
      title: "Synthesize interview themes",
      description: "Group interview findings into actionable themes and identify evidence for each insight.",
      status: "In Progress",
      priority: "High",
      due_date: "2026-09-15",
      created_at: "2026-08-30T08:45:00.000Z",
      updated_at: "2026-09-07T11:25:00.000Z"
    },
    {
      id: "task-5",
      workspace_id: "ws-research",
      title: "Schedule follow-up interviews",
      description: "Contact participants and confirm times for the second research round.",
      status: "To Do",
      priority: "Low",
      due_date: "2026-09-25",
      created_at: "2026-09-04T14:10:00.000Z",
      updated_at: "2026-09-04T14:10:00.000Z"
    },
    {
      id: "task-6",
      workspace_id: "ws-community",
      title: "Confirm venue for October meetup",
      description: "Compare venue options and confirm capacity, accessibility, and equipment.",
      status: "Done",
      priority: "High",
      due_date: "2026-08-30",
      created_at: "2026-08-10T09:30:00.000Z",
      updated_at: "2026-08-29T17:00:00.000Z"
    }
  ],
  notes: [
    {
      id: "note-1",
      workspace_id: "ws-design",
      title: "Navigation patterns",
      body: "Use a persistent primary navigation for core workflows. Keep secondary actions contextual and group destructive actions behind confirmation.",
      created_at: "2026-09-02T10:00:00.000Z",
      updated_at: "2026-09-08T09:45:00.000Z"
    },
    {
      id: "note-2",
      workspace_id: "ws-design",
      title: "Release meeting decisions",
      body: "The team agreed to prioritize accessibility fixes before adding new visual variants. Engineering will review the token migration plan next week.",
      created_at: "2026-09-06T13:25:00.000Z",
      updated_at: "2026-09-06T13:25:00.000Z"
    },
    {
      id: "note-3",
      workspace_id: "ws-research",
      title: "Interview quote bank",
      body: "Collect short, attributable quotes that illustrate the most common pain points. Tag each quote with the participant segment and research session.",
      created_at: "2026-08-29T15:15:00.000Z",
      updated_at: "2026-09-05T12:00:00.000Z"
    },
    {
      id: "note-4",
      workspace_id: "ws-community",
      title: "Volunteer onboarding",
      body: "Create a one-page guide covering event roles, communication channels, and the escalation process for day-of issues.",
      created_at: "2026-08-12T11:00:00.000Z",
      updated_at: "2026-08-20T14:30:00.000Z"
    }
  ],
  resources: [
    {
      id: "resource-1",
      workspace_id: "ws-design",
      title: "Bootstrap 5 documentation",
      url: "https://getbootstrap.com/docs/5.3/getting-started/introduction/",
      description: "Component, layout, and accessibility references for the interface implementation.",
      created_at: "2026-08-25T09:00:00.000Z",
      updated_at: "2026-09-01T10:00:00.000Z"
    },
    {
      id: "resource-2",
      workspace_id: "ws-design",
      title: "WCAG quick reference",
      url: "https://www.w3.org/WAI/WCAG22/quickref/",
      description: "Success criteria and techniques for accessible interface reviews.",
      created_at: "2026-08-26T09:20:00.000Z",
      updated_at: "2026-09-01T10:05:00.000Z"
    },
    {
      id: "resource-3",
      workspace_id: "ws-research",
      title: "Research repository guide",
      url: "https://www.nngroup.com/articles/repository/",
      description: "A practical starting point for organizing evidence and research outputs.",
      created_at: "2026-08-20T12:00:00.000Z",
      updated_at: "2026-08-31T16:20:00.000Z"
    },
    {
      id: "resource-4",
      workspace_id: "ws-community",
      title: "Event planning checklist",
      url: "https://www.example.com/event-planning",
      description: "A reusable checklist for venue, promotion, staffing, and follow-up tasks.",
      created_at: "2026-08-05T10:00:00.000Z",
      updated_at: "2026-08-15T11:00:00.000Z"
    }
  ],
  files: [
    {
      id: "file-1",
      workspace_id: "ws-design",
      filename: "component-audit.xlsx",
      upload_date: "2026-09-07T10:30:00.000Z",
      size: 248600
    },
    {
      id: "file-2",
      workspace_id: "ws-design",
      filename: "handoff-checklist.pdf",
      upload_date: "2026-09-03T14:00:00.000Z",
      size: 184320
    },
    {
      id: "file-3",
      workspace_id: "ws-research",
      filename: "interview-synthesis.docx",
      upload_date: "2026-09-05T09:45:00.000Z",
      size: 392100
    },
    {
      id: "file-4",
      workspace_id: "ws-community",
      filename: "venue-comparison.pdf",
      upload_date: "2026-08-28T12:15:00.000Z",
      size: 126800
    }
  ],
  activity: [
    {
      id: "activity-1",
      workspace_id: "ws-design",
      type: "task_updated",
      message: "Updated the accessibility audit task",
      timestamp: "2026-09-08T13:10:00.000Z"
    },
    {
      id: "activity-2",
      workspace_id: "ws-design",
      type: "note_updated",
      message: "Edited the navigation patterns note",
      timestamp: "2026-09-08T09:45:00.000Z"
    },
    {
      id: "activity-3",
      workspace_id: "ws-design",
      type: "resource_added",
      message: "Added the Bootstrap 5 documentation resource",
      timestamp: "2026-09-01T10:00:00.000Z"
    },
    {
      id: "activity-4",
      workspace_id: "ws-research",
      type: "task_updated",
      message: "Moved interview synthesis to In Progress",
      timestamp: "2026-09-07T11:25:00.000Z"
    },
    {
      id: "activity-5",
      workspace_id: "ws-research",
      type: "file_uploaded",
      message: "Added interview-synthesis.docx",
      timestamp: "2026-09-05T09:45:00.000Z"
    },
    {
      id: "activity-6",
      workspace_id: "ws-community",
      type: "task_completed",
      message: "Completed the venue confirmation task",
      timestamp: "2026-08-29T17:00:00.000Z"
    }
  ]
};

window.OneSpaceMockData.seed = function () {
  const collections = {
    onespace_users: window.OneSpaceMockData.users,
    onespace_workspaces: window.OneSpaceMockData.workspaces,
    onespace_tasks: window.OneSpaceMockData.tasks,
    onespace_notes: window.OneSpaceMockData.notes,
    onespace_resources: window.OneSpaceMockData.resources,
    onespace_files: window.OneSpaceMockData.files,
    onespace_activity: window.OneSpaceMockData.activity
  };

  Object.keys(collections).forEach(function (key) {
    try {
      if (!window.localStorage.getItem(key)) {
        window.localStorage.setItem(key, JSON.stringify(collections[key]));
      }
    } catch (error) {
      return;
    }
  });
};
