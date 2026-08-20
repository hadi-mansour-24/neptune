// Waiting the HTML page to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("searchForm");
  const resultsBody = document.getElementById("resultsBody");
  const exportBtn = document.querySelector(".export-btn");
  const favoritesBtn = document.getElementById("addToFavoritesBtn");

  let current_page = 1;
  let total_pages = 1;

  // Search form
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    current_page = 1;
    fetchArticles();
  });

  // Export button
  exportBtn.addEventListener("click", exportArticles);

  // Add to Favorites button
  favoritesBtn.addEventListener("click", addToFavorites);

  // Fetch articles
  function fetchArticles() {
    // Building the URL to fetch it from the backend endpoint (/search_articles)
    let url =
      `/search_articles?source=${form.source.value}` +
      `&keyword=${form.keyword.value}` +
      `&start_date=${form.start_date.value}` +
      `&end_date=${form.end_date.value}` +
      `&page=${current_page}&per_page=20`;

    fetch(url)
      .then((response) => response.json()) // Convert resopnse to JSON
      .then((data) => displayArticles(data)) // When ready call displayArticles function
      .catch((err) => console.error("Error:", err));
  }

  // Display articles
  function displayArticles(data) {
    resultsBody.innerHTML = ""; // Clear the table
    total_pages = data.total_pages;
    if (total_pages == 0) {
      resultsBody.innerHTML = "<h6 class='h6 center'>Ready for search!</h6>";
    }
    data.articles.forEach((article) => {
      let row = document.createElement("tr");
      // Store the ID of the article for uses like export or mark as favorite
      row.dataset.id = article.article_id;

      // Checkbox
      let cell1 = document.createElement("td");
      let cb = document.createElement("input");
      cb.type = "checkbox";
      cb.className = "article-checkbox";
      cell1.appendChild(cb);
      row.appendChild(cell1);

      // Journal
      let cell2 = document.createElement("td");
      cell2.textContent = article.source;
      row.appendChild(cell2);

      // Title with link
      let cell3 = document.createElement("td");
      if (article.article_url) {
        let link = document.createElement("a");
        link.href = article.article_url;
        link.target = "_blank";
        link.textContent = article.title;
        cell3.appendChild(link);
      }
      row.appendChild(cell3);

      // Content
      let cell4 = document.createElement("td");
      const fullContent = article.content || "";
      const contentId = `content-${article.article_id}`;

      let contentDiv = document.createElement("div");
      contentDiv.className = "content-cell";
      contentDiv.id = contentId;

      let contentText = document.createElement("div");
      contentText.className = "content-text";
      contentText.textContent = fullContent;
      contentText.onclick = (e) => expandContent(e, contentId);

      contentDiv.appendChild(contentText);
      cell4.appendChild(contentDiv);

      // Check if content is truncated after DOM update
      requestAnimationFrame(() => {
        let contentElement = document.getElementById(contentId);
        if (contentElement) {
          // max-height is 3.6em (3 lines at 1.2em line-height)
          // If scroll height > max-height, content is truncated
          if (contentElement.scrollHeight > 60) {
            contentElement.classList.add("is-truncated");
          }
        }
      });

      row.appendChild(cell4);

      // TEMPORARILY DISABLED: Images - media feature disabled, showing text-only content
      // let cell5 = document.createElement("td");
      // if (article.images && article.images.length > 0) {
      //   article.images.forEach((imgUrl) => {
      //     let imageName = imgUrl.split("/").pop();
      //     let displayName =
      //       imageName.length > 10
      //         ? imageName.substring(0, 10) + "..."
      //         : imageName;
      //
      //     let link = document.createElement("a");
      //     link.href = "#";
      //     link.textContent = displayName;
      //     link.title = imageName;
      //     link.className = "me-2";
      //     link.onclick = (e) => {
      //       e.preventDefault();
      //       openModal(imgUrl);
      //     };
      //     cell5.appendChild(link);
      //   });
      // } else {
      //   cell5.textContent = article.has_media ? "No images" : "No media";
      // }
      // row.appendChild(cell5);

      // Publish Date
      let cell6 = document.createElement("td");
      cell6.textContent = article.publish_date || "";
      row.appendChild(cell6);

      // Archive Date
      let cell7 = document.createElement("td");
      cell7.textContent = article.archive_date || "";
      row.appendChild(cell7);

      resultsBody.appendChild(row);
    });

    // Pagination
    addPagination();
  }

  function addPagination() {
    let row = document.createElement("tr");
    let cell = document.createElement("td");
    cell.colSpan = 7;
    cell.className = "py-4";

    // Create pagination container
    let paginationDiv = document.createElement("div");
    paginationDiv.className =
      "d-flex justify-content-center align-items-center gap-3";

    // Previous button
    let prevBtn = document.createElement("button");
    prevBtn.className = "btn btn-sm btn-outline-secondary";
    prevBtn.innerHTML = '<i class="bi bi-chevron-left me-1"></i>Previous';
    prevBtn.disabled = current_page <= 1;
    prevBtn.onclick = () => {
      if (current_page > 1) {
        current_page--;
        fetchArticles();
      }
    };

    // Page info
    let pageInfo = document.createElement("span");
    pageInfo.className = "fw-bold text-muted";
    pageInfo.textContent = `Page ${current_page} of ${total_pages}`;

    // Next button
    let nextBtn = document.createElement("button");
    nextBtn.className = "btn btn-sm btn-outline-secondary";
    nextBtn.innerHTML = 'Next<i class="bi bi-chevron-right ms-1"></i>';
    nextBtn.disabled = current_page >= total_pages;
    nextBtn.onclick = () => {
      if (current_page < total_pages) {
        current_page++;
        fetchArticles();
      }
    };

    paginationDiv.appendChild(prevBtn);
    paginationDiv.appendChild(pageInfo);
    paginationDiv.appendChild(nextBtn);
    cell.appendChild(paginationDiv);
    row.appendChild(cell);
    resultsBody.appendChild(row);
  }

  // Export articles
  function exportArticles() {
    // Selects all checkboxes that are checked
    let checkboxes = document.querySelectorAll(".article-checkbox:checked");

    if (checkboxes.length === 0) {
      alert("Please select articles first.");
      return;
    }

    // Loops through the checked checkboxes
    // and gets their IDs and adds them to the ids list
    let ids = [];
    checkboxes.forEach((cb) => {
      let row = cb.closest("tr");
      if (row && row.dataset.id) {
        ids.push(row.dataset.id);
      }
    });

    if (ids.length === 0) {
      alert("No articles selected.");
      return;
    }

    // Icon and placeholder for waiting of exporting
    exportBtn.innerHTML = '<i class="bi bi-hourglass"></i> Exporting...';
    exportBtn.disabled = true;

    // fetching the backend enpoint export excel with passing the extracted ids
    window.location.href = "/export_excel?ids=" + ids.join(",");

    setTimeout(() => {
      exportBtn.innerHTML =
        '<i class="bi bi-file-earmark-excel me-1"></i>Export';
      exportBtn.disabled = false;
    }, 3000);
  }

  // Add selected articles to favorites
  function addToFavorites() {
    // Prevent double submissions
    if (favoritesBtn.disabled) {
      return;
    }

    let checkboxes = document.querySelectorAll(".article-checkbox:checked");

    if (checkboxes.length === 0) {
      return;
    }

    let ids = [];
    checkboxes.forEach((cb) => {
      let row = cb.closest("tr");
      if (row && row.dataset.id) {
        ids.push(row.dataset.id);
      }
    });

    if (ids.length === 0) {
      return;
    }

    // Create FormData and submit via AJAX
    let formData = new FormData();
    ids.forEach((id) => {
      formData.append("article_ids", id);
    });

    // Disable button to prevent double submission
    favoritesBtn.disabled = true;
    favoritesBtn.innerHTML =
      '<i class="bi bi-hourglass-split me-1"></i>Adding...';

    fetch("/add_favorites", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Uncheck all checkboxes
          document
            .querySelectorAll(".article-checkbox:checked")
            .forEach((cb) => {
              cb.checked = false;
            });

          // Show toast-like feedback (optional)
          console.log(data.message);
        } else {
          console.error(
            "Error: " + (data.message || "Failed to add favorites"),
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      })
      .finally(() => {
        // Re-enable button after request completes
        favoritesBtn.disabled = false;
        favoritesBtn.innerHTML =
          '<i class="bi bi-star me-1"></i>Add to Favorites';
      });
  }
  fetchArticles();
});

// TEMPORARILY DISABLED: Open image modal functionality - media display feature disabled
// function openModal(imgUrl) {
//   document.getElementById("modalImg").src = imgUrl;
//   document.getElementById("downloadLink").href = imgUrl;
//   document.getElementById("downloadLink").download = imgUrl.split("/").pop();
//
//   new bootstrap.Modal(document.getElementById("imageModal")).show();
// }

// Toggle content expand/collapse
function toggleContent(articleId) {
  const previewDiv = document.getElementById(`preview-${articleId}`);
  const fullDiv = document.getElementById(`full-${articleId}`);

  if (previewDiv.style.display === "none") {
    previewDiv.style.display = "block";
    fullDiv.style.display = "none";
  } else {
    previewDiv.style.display = "none";
    fullDiv.style.display = "block";
  }
}

// Expand content on click
function expandContent(event, contentId) {
  event.stopPropagation();
  const contentCell = document.getElementById(contentId);
  contentCell.classList.toggle("expanded");
}
