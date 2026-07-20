/**
 * Owner Dashboard JavaScript
 * Automated dashboards for listing expiration and mismatch detection
 */

let dashboardData = null;

// Load dashboard data
async function loadDashboard() {
  console.log("loadDashboard called");
  console.log("API endpoint:", API);

  try {
    const token = localStorage.getItem("prom_token");
    console.log("Token exists:", !!token);

    const url = `${API}/owner/dashboard`;
    console.log("Fetching from:", url);

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("Response status:", res.status);

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Error response:", errorText);
      throw new Error(`Failed to load dashboard: ${res.status}`);
    }

    dashboardData = await res.json();
    console.log("Dashboard data loaded:", dashboardData);

    renderExpirationDashboard();
    renderMismatchDashboard();

    // Update last synced time
    const lastUpdated = new Date(dashboardData.last_updated);
    document.getElementById("last-synced").textContent =
      `Last synced: ${lastUpdated.toLocaleString()}`;
  } catch (err) {
    console.error("Error loading dashboard:", err);

    // Show error in UI
    const expContainer = document.getElementById("expiration-dashboard");
    const mismatchContainer = document.getElementById("mismatch-dashboard");

    if (expContainer) {
      expContainer.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--ibm-red);">
        <p><strong>Error loading dashboard</strong></p>
        <p style="font-size: 13px; margin-top: 0.5rem;">${err.message}</p>
        <p style="font-size: 13px;">Check browser console for details.</p>
      </div>`;
    }

    if (mismatchContainer) {
      mismatchContainer.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--ibm-red);">
        <p>Error loading mismatch data</p>
      </div>`;
    }
  }
}

// Render Expiration Dashboard
function renderExpirationDashboard() {
  const container = document.getElementById("expiration-dashboard");
  const data = dashboardData.expiration_dashboard;

  const categories = [
    {
      key: "expired",
      title: "Expired",
      color: "var(--ibm-red)",
      bgColor: "var(--ibm-red-light)",
      description: "Hidden from candidates",
    },
    {
      key: "soon",
      title: "Expiring Soon",
      subtitle: "≤7 days",
      color: "var(--ibm-orange)",
      bgColor: "var(--ibm-orange-light)",
      description: "Urgent action needed",
    },
    {
      key: "15_days",
      title: "15 Days Left",
      subtitle: "8-15 days",
      color: "#f1c21b",
      bgColor: "#fef7e0",
      description: "Review soon",
    },
    {
      key: "30_days",
      title: "30 Days Left",
      subtitle: "16+ days",
      color: "var(--ibm-green)",
      bgColor: "var(--ibm-green-light)",
      description: "All good",
    },
  ];

  let html = '<div class="dashboard-categories-grid">';

  categories.forEach((cat) => {
    const listings = data[cat.key] || [];
    const count = listings.length;

    html += `
      <div class="dashboard-category-tab">
        <div class="dashboard-tab-header" style="border-top: 3px solid ${cat.color}; background: ${cat.bgColor};">
          <div class="dashboard-tab-badge" style="background: ${cat.color};">
            ${count}
          </div>
          <h3 style="color: ${cat.color}; margin: 0; font-size: 14px;">${cat.title}</h3>
          ${cat.subtitle ? `<p style="font-size: 11px; color: var(--text-secondary); margin: 0.25rem 0 0 0;">${cat.subtitle}</p>` : ''}
        </div>
        <div class="dashboard-tab-body" id="exp-${cat.key}">
          ${renderExpirationListings(listings, cat.key)}
        </div>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

// Render listings for expiration category
function renderExpirationListings(listings, category) {
  if (listings.length === 0) {
    return `<p class="text-muted" style="padding: 1rem;">No listings in this category</p>`;
  }

  console.log(`Rendering ${listings.length} listings for category ${category}:`, listings);

  let html = "";
  listings.forEach((seat) => {
    console.log('Seat data:', seat);
    console.log('Seat ID:', seat.seat_id);
    console.log('Title:', seat.title);

    const daysLeft = seat.days_until_expiration;
    const daysText = daysLeft < 0
      ? `Expired ${Math.abs(daysLeft)} days ago`
      : `${daysLeft} days left`;

    const isExpired = daysLeft < 0;
    const isUrgent = daysLeft > 0 && daysLeft <= 7;

    html += `
      <div class="dashboard-listing-item">
        ${isExpired ? `
          <div class="dashboard-listing-status-banner expired-banner">
            ${daysText}
          </div>
        ` : isUrgent ? `
          <div class="dashboard-listing-status-banner urgent-banner">
            ${daysText}
          </div>
        ` : ''}
        <div class="dashboard-listing-content">
          <div class="dashboard-listing-info">
            <div class="dashboard-listing-title">${seat.title || 'Untitled'}</div>
            <div class="dashboard-listing-meta">${seat.client_name || seat.client || 'Client'} · ${seat.work_location || seat.location || 'Location TBD'}</div>
            ${!isExpired && !isUrgent ? `<div class="dashboard-listing-meta">${daysText}</div>` : ''}
          </div>
          <div class="dashboard-listing-actions">
            ${category === "expired"
              ? `<button class="btn btn-primary btn-sm" onclick="reactivateListing('${seat.seat_id}')">Reactivate</button>
                 <button class="btn btn-secondary btn-sm" onclick="viewListingDetails('${seat.seat_id}')">View Details</button>
                 <button class="btn btn-ghost btn-sm" onclick="archiveListing('${seat.seat_id}')" style="color: var(--text-muted);">Archive</button>`
              : `<button class="btn btn-primary btn-sm" onclick="confirmListing('${seat.seat_id}')">Confirm Active</button>
                 <button class="btn btn-secondary btn-sm" onclick="viewListingDetails('${seat.seat_id}')">View Details</button>`
            }
          </div>
        </div>
      </div>
    `;
  });

  return html;
}

// Render Mismatch Dashboard
function renderMismatchDashboard() {
  const container = document.getElementById("mismatch-dashboard");
  const mismatches = dashboardData.mismatch_dashboard;

  if (mismatches.length === 0) {
    container.innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <p style="color: var(--ibm-green); font-weight: 600; margin: 0;">No alerts</p>
        <p class="text-muted" style="margin: 0.5rem 0 0 0; font-size: 13px;">All listings have appropriate candidate counts</p>
      </div>
    `;
    return;
  }

  let html = '<div class="dashboard-categories-grid" style="grid-template-columns: 1fr;">';

  html += `
    <div class="dashboard-category-tab">
      <div class="dashboard-tab-header" style="border-top: 3px solid var(--ibm-purple); background: var(--ibm-purple-light);">
        <div class="dashboard-tab-badge" style="background: var(--ibm-purple);">
          ${mismatches.length}
        </div>
        <h3 style="color: var(--ibm-purple); margin: 0; font-size: 14px;">Capacity Alert</h3>
        <p style="font-size: 11px; color: var(--text-secondary); margin: 0.25rem 0 0 0;">Enough selected candidates</p>
      </div>
      <div class="dashboard-tab-body">
  `;

  mismatches.forEach((mismatch) => {
    const seat = mismatch.seat;
    const client = seat.client_name || seat.client || 'Client';
    const location = seat.work_location || seat.location || 'Location TBD';

    html += `
      <div class="dashboard-listing-item">
        <div class="dashboard-listing-content" style="align-items: center;">
          <div style="flex: 1;">
            <div class="dashboard-listing-title">${seat.title || 'Untitled'}</div>
            <div class="dashboard-listing-meta">${client} · ${location}</div>
            <div style="margin-top: 0.5rem; padding: 0.5rem; background: var(--ibm-purple-light); color: var(--ibm-purple); border-radius: 4px; display: inline-block; font-size: 12px; font-weight: 600;">
              ${mismatch.selected_count} selected / ${mismatch.positions_available} needed
            </div>
          </div>
          <div class="dashboard-listing-actions">
            <button class="btn btn-primary btn-sm" onclick="closeListing('${seat.seat_id}')">Close Listing</button>
            <button class="btn btn-secondary btn-sm" onclick="markAsFormal('${seat.seat_id}')">Mark as Formality</button>
            <button class="btn btn-secondary btn-sm" onclick="editListing('${seat.seat_id}')">Edit Listing</button>
          </div>
        </div>
      </div>
    `;
  });

  html += `
      </div>
    </div>
  </div>`;

  container.innerHTML = html;
}

// Actions
async function confirmListing(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/confirm-listing`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ seat_id: seatId }),
    });

    if (!res.ok) throw new Error("Failed to confirm listing");

    showToast("Listing confirmed for 30 more days", "success");
    loadDashboard(); // Reload dashboard
  } catch (err) {
    console.error("Error confirming listing:", err);
    showToast("Failed to confirm listing", "error");
  }
}

async function reactivateListing(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/reactivate-listing/${seatId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Failed to reactivate listing");

    showToast("Listing reactivated", "success");
    loadDashboard();
  } catch (err) {
    console.error("Error reactivating listing:", err);
    showToast("Failed to reactivate listing", "error");
  }
}

async function closeListing(seatId) {
  if (!confirm("Are you sure you want to close this listing?")) return;

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/close-listing/${seatId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Failed to close listing");

    showToast("Listing closed", "success");
    loadDashboard();
  } catch (err) {
    console.error("Error closing listing:", err);
    showToast("Failed to close listing", "error");
  }
}

async function markAsFormal(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/update-listing-type`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        seat_id: seatId,
        seat_type: "formal",
      }),
    });

    if (!res.ok) throw new Error("Failed to update listing type");

    showToast("Listing marked as formality posting", "success");
    loadDashboard();
  } catch (err) {
    console.error("Error updating listing type:", err);
    showToast("Failed to update listing type", "error");
  }
}

function viewListingDetails(seatId) {
  console.log('viewListingDetails called with seatId:', seatId);
  // Navigate to listing details with backend port
  const backendPort = localStorage.getItem('BACKEND_PORT') || '8000';
  const url = `seat-detail.html?id=${encodeURIComponent(seatId)}&backend_port=${backendPort}`;
  console.log('Navigating to:', url);
  window.location.href = url;
}

function editListing(seatId) {
  // Show edit modal with current listing data
  showEditListingModal(seatId);
}

function viewApplicants(seatId) {
  // Show applicants modal or navigate
  showApplicantsModal(seatId);
}

async function archiveListing(seatId) {
  if (!confirm("Archive this listing? It will be permanently hidden from the dashboard.")) return;

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/close-listing/${seatId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Failed to archive listing");

    showToast("Listing archived", "success");
    loadDashboard();
  } catch (err) {
    console.error("Error archiving listing:", err);
    showToast("Failed to archive listing", "error");
  }
}

// Toggle category expand/collapse
function toggleCategory(categoryId) {
  const body = document.getElementById(categoryId);
  const arrow = document.getElementById('arrow-' + categoryId);

  if (body.classList.contains('collapsed')) {
    body.classList.remove('collapsed');
    arrow.textContent = '▲';
  } else {
    body.classList.add('collapsed');
    arrow.textContent = '▼';
  }
}

// Edit Listing Modal
async function showEditListingModal(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/seats/${seatId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Failed to load listing");
    const seat = await res.json();

    const modalHtml = `
      <div id="edit-modal-overlay" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;" onclick="closeEditModal(event)">
        <div class="card" style="max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto;" onclick="event.stopPropagation()">
          <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <span class="card-title">Edit Listing</span>
            <button onclick="closeEditModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text-muted);">&times;</button>
          </div>
          <form id="edit-listing-form" onsubmit="submitEditListing(event, '${seatId}')">
            <div style="padding: 0 1.25rem 1.25rem 1.25rem;">
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Position Title *</label>
                <input type="text" class="form-input" id="edit-title" value="${seat.title}" required />
              </div>
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Client Name *</label>
                <input type="text" class="form-input" id="edit-client" value="${seat.client_name}" required />
              </div>
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Work Location *</label>
                <input type="text" class="form-input" id="edit-location" value="${seat.work_location}" required />
              </div>
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Positions Needed *</label>
                <input type="number" class="form-input" id="edit-positions" value="${seat.positions_still_needed}" required min="1" />
              </div>
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Band Low</label>
                <input type="text" class="form-input" id="edit-band-low" value="${seat.requested_band_low || ''}" />
              </div>
              <div style="margin-bottom: 1rem;">
                <label class="form-label">Band High</label>
                <input type="text" class="form-input" id="edit-band-high" value="${seat.requested_band_high || ''}" />
              </div>
              <div style="display: flex; gap: 0.75rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                <button type="submit" class="btn btn-primary">Save Changes</button>
                <button type="button" class="btn btn-ghost" onclick="closeEditModal()">Cancel</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  } catch (err) {
    console.error("Error loading listing:", err);
    showToast("Failed to load listing", "error");
  }
}

function closeEditModal(event) {
  if (!event || event.target.id === 'edit-modal-overlay') {
    const modal = document.getElementById('edit-modal-overlay');
    if (modal) modal.remove();
  }
}

async function submitEditListing(event, seatId) {
  event.preventDefault();

  const updates = {
    title: document.getElementById('edit-title').value,
    client_name: document.getElementById('edit-client').value,
    work_location: document.getElementById('edit-location').value,
    positions_still_needed: parseInt(document.getElementById('edit-positions').value),
    requested_band_low: document.getElementById('edit-band-low').value,
    requested_band_high: document.getElementById('edit-band-high').value,
  };

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API}/owner/update-listing/${seatId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });

    if (!res.ok) throw new Error("Failed to update listing");

    showToast("Listing updated successfully", "success");
    closeEditModal();
    loadDashboard();
  } catch (err) {
    console.error("Error updating listing:", err);
    showToast("Failed to update listing", "error");
  }
}

// Initialize dashboard on page load
window.addEventListener("load", () => {
  console.log("Page loaded, checking if on owner page...");
  console.log("Current path:", window.location.pathname);

  // Check if we're on owner page and have auth
  if (window.location.pathname.includes("owner.html")) {
    console.log("On owner page");

    const token = localStorage.getItem("prom_token");
    console.log("Has token:", !!token);

    // Check if dashboard containers exist
    const expContainer = document.getElementById("expiration-dashboard");
    const mismatchContainer = document.getElementById("mismatch-dashboard");
    console.log("Containers exist:", !!expContainer, !!mismatchContainer);

    if (token && expContainer && mismatchContainer) {
      console.log("Loading dashboard...");
      loadDashboard();

      // Auto-refresh every 5 minutes
      setInterval(loadDashboard, 5 * 60 * 1000);
    } else {
      console.error("Missing requirements:", {
        token: !!token,
        expContainer: !!expContainer,
        mismatchContainer: !!mismatchContainer
      });
    }
  } else {
    console.log("Not on owner page");
  }
});
