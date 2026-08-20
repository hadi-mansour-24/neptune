document.addEventListener("DOMContentLoaded", () => {
  // Load initial data
  loadCrawlers();
  loadLogs();
  loadUsers();
  updateDashboardStats();

  // Load current username for change username form
  loadCurrentUsername();

  // Setup form event listeners
  setupFormListeners();

  // Setup button event listeners
  setupButtonListeners();
});

// Load current username for the change username form
function loadCurrentUsername() {
  fetch("/get_current_user")
    .then((res) => res.json())
    .then((data) => {
      if (data.success && data.username) {
        document.getElementById("currentUsername").value = data.username;
      }
    })
    .catch((err) => console.error("Error loading current username:", err));
}

// Setup form event listeners
function setupFormListeners() {
  // Add Crawler Form
  document.getElementById("addCrawlerForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    addCrawler();
  });

  // Create User Form
  document.getElementById("createUserForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    createUser();
  });

  // Change Username Form
  document
    .getElementById("changeUsernameForm")
    ?.addEventListener("submit", (e) => {
      e.preventDefault();
      changeUsername();
    });

  // Change Password Form
  document
    .getElementById("changePasswordForm")
    ?.addEventListener("submit", (e) => {
      e.preventDefault();
      changePassword();
    });
}

// Setup button event listeners
function setupButtonListeners() {
  // Refresh buttons
  document.getElementById("refreshAllBtn")?.addEventListener("click", () => {
    refreshAllData();
  });

  document.getElementById("refreshLogsBtn")?.addEventListener("click", () => {
    loadLogs();
  });

  // Export Logs Button
  document.getElementById("exportLogsBtn")?.addEventListener("click", () => {
    exportLogs();
  });

  // Clear Logs Button
  document.getElementById("clearLogsBtn")?.addEventListener("click", () => {
    clearLogs();
  });

  // Log Level Filter
  document.getElementById("logLevelFilter")?.addEventListener("change", (e) => {
    filterLogsByLevel(e.target.value);
  });
}

// Update dashboard statistics
function updateDashboardStats() {
  // Update active crawlers count
  fetch("/get_crawlers")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const activeCrawlers = data.crawlers.filter(
          (c) => c.status === "active" || c.last_seen !== "Never",
        ).length;
        document.getElementById("activeCrawlersCount").textContent =
          activeCrawlers;
      }
    })
    .catch((err) => console.error("Error updating crawler stats:", err));

  // Update total users count
  fetch("/get_users")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("totalUsersCount").textContent =
          data.users.length;
      }
    })
    .catch((err) => console.error("Error updating user stats:", err));

  // Update total logs count
  fetch("/get_logs_count")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("totalLogsCount").textContent = data.count;
      }
    })
    .catch((err) => console.error("Error updating logs stats:", err));
}

// Load crawlers - Updated to match backend response structure
function loadCrawlers() {
  fetch("/get_crawlers")
    .then((res) => res.json())
    .then((data) => {
      const tbody = document.getElementById("crawlerTableBody");
      tbody.innerHTML = "";

      if (!data.success || data.crawlers.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5">
                            <i class="bi bi-robot me-2"></i>
                            <span class="text-muted">No crawlers configured</span>
                        </td>
                    </tr>`;
        return;
      }

      data.crawlers.forEach((crawler) => {
        const row = document.createElement("tr");

        // Crawler Name
        const nameCell = document.createElement("td");
        nameCell.className = "fw-bold";
        nameCell.textContent = crawler.name;

        // Status (determined by last_seen)
        const statusCell = document.createElement("td");
        const isActive =
          crawler.last_seen !== "Never" &&
          new Date() - new Date(crawler.last_seen) < 5 * 60 * 1000; // 5 minutes
        const statusBadge = isActive
          ? '<span class="badge bg-success"><i class="bi bi-circle-fill me-1"></i>Active</span>'
          : '<span class="badge bg-secondary"><i class="bi bi-circle me-1"></i>Inactive</span>';
        statusCell.innerHTML = statusBadge;

        // Last Seen
        const lastSeenCell = document.createElement("td");
        lastSeenCell.innerHTML = `<span class="text-muted small">${crawler.last_seen}</span>`;

        // Actions
        const actionsCell = document.createElement("td");
        actionsCell.className = "text-end";

        const runButton = document.createElement("button");
        runButton.className = "btn btn-sm btn-outline-secondary me-2";
        runButton.innerHTML = '<i class="bi bi-play me-1"></i>Run';
        runButton.onclick = () =>
          runCrawler(crawler.id, crawler.name, runButton);

        actionsCell.appendChild(runButton);

        row.appendChild(nameCell);
        row.appendChild(statusCell);
        row.appendChild(lastSeenCell);
        row.appendChild(actionsCell);

        tbody.appendChild(row);
      });

      updateDashboardStats();
    })
    .catch((err) => {
      console.error("Error loading crawlers:", err);
      document.getElementById("crawlerTableBody").innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5 text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Failed to load crawlers
                    </td>
                </tr>`;
    });
}

// Load logs - Updated to match backend response structure
function loadLogs() {
  fetch("/get_logs")
    .then((res) => res.json())
    .then((data) => {
      const tbody = document.getElementById("logsTableBody");
      tbody.innerHTML = "";

      if (!data.success || data.logs.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5">
                            <i class="bi bi-inbox me-2"></i>
                            <span class="text-muted">No logs available</span>
                        </td>
                    </tr>`;
        return;
      }

      // Ensure logs are sorted by timestamp in descending order (newest first)
      const sortedLogs = data.logs.sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
      });

      sortedLogs.forEach((log) => {
        const row = document.createElement("tr");

        // Determine badge class based on log level
        let badgeClass = "bg-secondary";
        let iconClass = "bi-info-circle";

        if (log.level === "URGENT" || log.level === "ERROR") {
          badgeClass = "bg-danger";
          iconClass = "bi-exclamation-triangle";
        } else if (log.level === "MODERATE" || log.level === "WARNING") {
          badgeClass = "bg-warning";
          iconClass = "bi-exclamation-circle";
        } else if (log.level === "INFO") {
          badgeClass = "bg-info";
          iconClass = "bi-info-circle";
        } else if (log.level === "SUCCESS") {
          badgeClass = "bg-success";
          iconClass = "bi-check-circle";
        }

        // Timestamp
        const timestampCell = document.createElement("td");
        timestampCell.innerHTML = `
                    <div class="small text-muted">${log.timestamp}</div>
                `;

        // Crawler (Journal)
        const crawlerCell = document.createElement("td");
        crawlerCell.innerHTML = `
                    <span class="badge bg-light text-dark border">
                        <i class="bi bi-robot me-1"></i>${log.journal}
                    </span>
                `;

        // Level
        const levelCell = document.createElement("td");
        levelCell.innerHTML = `
                    <span class="badge ${badgeClass}">
                        <i class="bi ${iconClass} me-1"></i>${log.level}
                    </span>
                `;

        // Message
        const messageCell = document.createElement("td");
        messageCell.className = "small";
        messageCell.textContent = log.message;

        row.appendChild(timestampCell);
        row.appendChild(crawlerCell);
        row.appendChild(levelCell);
        row.appendChild(messageCell);

        tbody.appendChild(row);
      });

      updateDashboardStats();
    })
    .catch((err) => {
      console.error("Error loading logs:", err);
      document.getElementById("logsTableBody").innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5 text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Failed to load logs
                    </td>
                </tr>`;
    });
}

// Load users - Updated to match backend response structure
function loadUsers() {
  fetch("/get_users")
    .then((res) => res.json())
    .then((data) => {
      const tbody = document.getElementById("usersTableBody");
      tbody.innerHTML = "";

      if (!data.success || data.users.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5">
                            <i class="bi bi-people me-2"></i>
                            <span class="text-muted">No users found</span>
                        </td>
                    </tr>`;
        return;
      }

      data.users.forEach((user) => {
        const row = document.createElement("tr");

        // Username
        const usernameCell = document.createElement("td");
        usernameCell.className = "fw-bold";
        usernameCell.textContent = user.username;

        // Role
        const roleCell = document.createElement("td");
        const roleBadge =
          user.role === "admin" || user.role === "super"
            ? '<span class="badge bg-success"><i class="bi bi-shield-check me-1"></i>Admin</span>'
            : '<span class="badge bg-secondary"><i class="bi bi-person me-1"></i>User</span>';
        roleCell.innerHTML = roleBadge;

        // Created At
        const createdAtCell = document.createElement("td");
        createdAtCell.innerHTML = `
                    <div class="small text-muted">${user.created_at}</div>
                `;

        // Actions
        const actionsCell = document.createElement("td");
        actionsCell.className = "text-end";

        // Only allow deleting user accounts (not admin accounts)
        if (user.role === "user") {
          const deleteButton = document.createElement("button");
          deleteButton.className = "btn btn-sm btn-outline-danger";
          deleteButton.innerHTML = '<i class="bi bi-trash me-1"></i>Delete';
          deleteButton.onclick = () => deleteUser(user.id, user.username);
          actionsCell.appendChild(deleteButton);
        } else if (user.role === "admin") {
          const deleteButton = document.createElement("button");
          deleteButton.className = "btn btn-sm btn-outline-danger";
          deleteButton.innerHTML = '<i class="bi bi-trash me-1"></i>Delete';
          deleteButton.onclick = () => deleteUser(user.id, user.username);
          actionsCell.appendChild(deleteButton);
        } else {
          const deleteButton = document.createElement("span");
          // <span class="badge bg-success"><i class="bi bi-circle-fill me-1"></i>Active</span>
          deleteButton.className = "badge bg-danger";
          deleteButton.innerHTML = `Unauthorized`;
          actionsCell.appendChild(deleteButton);
        }

        row.appendChild(usernameCell);
        row.appendChild(roleCell);
        row.appendChild(createdAtCell);
        row.appendChild(actionsCell);

        tbody.appendChild(row);
      });

      updateDashboardStats();
    })
    .catch((err) => {
      console.error("Error loading users:", err);
      document.getElementById("usersTableBody").innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5 text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Failed to load users
                    </td>
                </tr>`;
    });
}

// Add new crawler
function addCrawler() {
  const name = document.getElementById("crawlerName").value;

  if (!name) {
    showAlert("Please enter a crawler name", "warning");
    return;
  }

  fetch("/add_crawler", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: name }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        // Close modal
        bootstrap.Modal.getInstance(
          document.getElementById("addCrawlerModal"),
        ).hide();
        // Reset form
        document.getElementById("addCrawlerForm").reset();
        // Reload crawlers
        loadCrawlers();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error adding crawler:", err);
      showAlert("Network error while adding crawler", "danger");
    });
}

// Create new user
function createUser() {
  const username = document.getElementById("newUsername").value;
  const password = document.getElementById("newUserPassword").value;
  const role = document.getElementById("userRole").value;

  if (!username || !password) {
    showAlert("Please fill in all required fields", "warning");
    return;
  }

  fetch("/create_user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: username,
      password: password,
      role: role,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        // Close modal
        bootstrap.Modal.getInstance(
          document.getElementById("createUserModal"),
        ).hide();
        // Reset form
        document.getElementById("createUserForm").reset();
        // Reload users
        loadUsers();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error creating user:", err);
      showAlert("Network error while creating user", "danger");
    });
}

// Change username
function changeUsername() {
  const newUsername = document.getElementById("updatedUsername").value;

  if (!newUsername) {
    showAlert("Please enter a new username", "warning");
    return;
  }

  fetch("/change_username", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      new_username: newUsername,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        // Close modal
        bootstrap.Modal.getInstance(
          document.getElementById("changeUsernameModal"),
        ).hide();
        // Reset form
        document.getElementById("changeUsernameForm").reset();
        // Update current username display
        loadCurrentUsername();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error changing username:", err);
      showAlert("Network error while changing username", "danger");
    });
}

// Change password
function changePassword() {
  const currentPassword = document.getElementById("old_password").value;
  const newPassword = document.getElementById("adminNewPassword").value;
  const confirmPassword = document.getElementById("adminConfirmPassword").value;

  if (!currentPassword || !newPassword || !confirmPassword) {
    showAlert("Please fill in all fields", "warning");
    return;
  }

  if (newPassword !== confirmPassword) {
    showAlert("New passwords do not match", "warning");
    return;
  }

  fetch("/change_password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      old_password: currentPassword,
      new_password: newPassword,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        // Close modal
        bootstrap.Modal.getInstance(
          document.getElementById("changePasswordModal"),
        ).hide();
        // Reset form
        document.getElementById("changePasswordForm").reset();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error changing password:", err);
      showAlert("Network error while changing password", "danger");
    });
}

// Run crawler
function runCrawler(crawlerId, crawlerName, button) {
  button.disabled = true;
  const originalHTML = button.innerHTML;
  button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Running...';

  fetch("/run_crawler", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ crawler_id: crawlerId }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(`${crawlerName} has been started successfully!`, "success");
        // Reload crawlers to update status
        setTimeout(() => loadCrawlers(), 1000);
      } else {
        showAlert(`Error: ${data.message}`, "danger");
      }
      // Reset button
      button.disabled = false;
      button.innerHTML = originalHTML;
    })
    .catch((err) => {
      console.error("Error running crawler:", err);
      showAlert("Error running crawler", "danger");
      button.disabled = false;
      button.innerHTML = originalHTML;
    });
}

// Delete user
function deleteUser(userId, username) {
  if (!confirm(`Are you sure you want to delete user '${username}'?`)) {
    return;
  }

  fetch(`/delete_user/${userId}`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        loadUsers();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error deleting user:", err);
      showAlert("Network error while deleting user", "danger");
    });
}

// Clear logs
function clearLogs() {
  if (!confirm("Are you sure you want to clear all system logs?")) return;

  fetch("/clear_logs", {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(data.message, "success");
        loadLogs();
      } else {
        showAlert(data.message, "danger");
      }
    })
    .catch((err) => {
      console.error("Error clearing logs:", err);
      showAlert("Error clearing logs", "danger");
    });
}

// Export logs
function exportLogs() {
  fetch("/export_logs")
    .then((res) => res.blob())
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `logs_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      showAlert("Logs exported successfully", "success");
    })
    .catch((err) => {
      console.error("Error exporting logs:", err);
      showAlert("Error exporting logs", "danger");
    });
}

// Filter logs by level
function filterLogsByLevel(level) {
  const rows = document.querySelectorAll("#logsTableBody tr");
  rows.forEach((row) => {
    const levelCell = row.querySelector("td:nth-child(3)");
    if (levelCell) {
      const logLevel = levelCell.textContent.trim();
      if (level === "all" || logLevel === level.toUpperCase()) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    }
  });
}

// Refresh all data
function refreshAllData() {
  showAlert("Refreshing all data...", "info");
  loadCrawlers();
  loadLogs();
  loadUsers();
  updateDashboardStats();
}

// Helper function to show alerts
function showAlert(message, type) {
  // Remove existing alerts
  const existingAlert = document.querySelector(".alert-dismissible");
  if (existingAlert) {
    existingAlert.remove();
  }

  // Create new alert
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  alertDiv.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        max-width: 400px;
    `;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(alertDiv);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 5000);
}
