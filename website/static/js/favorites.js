// Load favorites when page opens
loadFavorites();

// Refresh button click
document.getElementById("refreshBtn").onclick = loadFavorites;

// Export button click
document.getElementById("exportBtn").onclick = function (e) {
  // Show loading on export button
  const originalText = this.innerHTML;
  this.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Exporting...';
  this.disabled = true;

  // Button will reset after download starts
  setTimeout(() => {
    this.innerHTML = originalText;
    this.disabled = false;
  }, 2000);
};

// Load favorites from server
function loadFavorites() {
  // Show loading
  document.getElementById("loading").style.display = "block";
  document.getElementById("resultsCard").style.display = "none";
  document.getElementById("emptyState").style.display = "none";

  // Get favorites from server
  fetch("/get_favorites")
    .then((response) => response.json())
    .then((articles) => {
      document.getElementById("loading").style.display = "none";

      if (articles.length === 0) {
        // Show "no favorites" message
        document.getElementById("emptyState").style.display = "block";
      } else {
        document.getElementById("resultsCard").style.display = "block";
        // Add each article as a table row
        displayArticles(articles);
      }
    })
    .catch((error) => {
      console.log("Error:", error);
      document.getElementById("loading").style.display = "none";
      alert("Error loading favorites");
    });
}

// Display articles in table
function displayArticles(articles) {
  const tbody = document.getElementById("favoritesBody");
  tbody.innerHTML = "";

  articles.forEach((article) => {
    const row = document.createElement("tr");

    // Truncate content to reasonable length
    let displayContent = article.content || "No content available";
    if (displayContent.length > 100) {
      displayContent = displayContent.substring(0, 100) + "...";
    }

    // TEMPORARILY DISABLED: Build media links - media feature disabled for text-only content
    // let mediaHtml = "";
    // if (article.images && article.images.length > 0) {
    //   mediaHtml = article.images
    //     .map((img) => {
    //       const filename = img.split("/").pop();
    //       const displayName =
    //         filename.length > 10 ? filename.substring(0, 10) + "..." : filename;
    //       return `<a href="#" onclick="showImage('${img}'); return false;" title="${filename}" class="badge bg-secondary me-1 mb-1 d-inline-block">
    //         <i class="bi bi-image me-1"></i>${displayName}
    //       </a>`;
    //     })
    //     .join("");
    // } else {
    //   mediaHtml = '<span class="text-muted">—</span>';
    // }

    row.innerHTML = `
      <td>
        <small class="fw-bold text-dark">${article.source || "Unknown"}</small>
      </td>
      <td>
        <a href="${article.article_url}" target="_blank" class="text-decoration-none fw-bold">
          ${article.title}
        </a>
      </td>
      <td>
        <div class="content-cell" style="max-height: 3.6em; overflow: hidden;">
          <small class="text-muted">${displayContent}</small>
        </div>
      </td>
      <td>
        <small class="text-muted">${article.publish_date || "—"}</small>
      </td>
      <td class="text-center">
        <button class="btn btn-sm btn-outline-danger" onclick="removeFavorite('${article.article_id}', this)" title="Remove from favorites">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;

    tbody.appendChild(row);
  });
}

// Show image in modal
function showImage(imgUrl) {
  document.getElementById("modalImg").src = imgUrl;
  document.getElementById("downloadLink").href = imgUrl;
  new bootstrap.Modal(document.getElementById("imageModal")).show();
}

// Remove from favorites
function removeFavorite(articleId, button) {
  if (!confirm("Remove this article from favorites?")) return;

  // Disable button
  button.disabled = true;
  button.innerHTML = '<i class="bi bi-hourglass-split"></i>';

  fetch(`/remove_favorite/${articleId}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Remove row from page
        const row = button.closest("tr");
        row.style.opacity = "0.5";
        setTimeout(() => {
          row.remove();

          // If no rows left, reload page
          if (document.querySelectorAll("#favoritesBody tr").length === 0) {
            document.getElementById("resultsCard").style.display = "none";
            document.getElementById("emptyState").style.display = "block";
          }
        }, 300);
      } else {
        alert("Error: " + data.message);
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-trash"></i>';
      }
    })
    .catch(() => {
      alert("Network error");
      button.disabled = false;
      button.innerHTML = '<i class="bi bi-trash"></i>';
    });
}
