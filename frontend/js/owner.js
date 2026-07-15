/**
 * Owner Portal JavaScript
 * Handles owner-specific functionality for listing management
 */

const API_BASE = "http://127.0.0.1:8000/api";

// ── Authentication ────────────────────────────────────────────────────────────
function checkOwnerAuth() {
  const token = localStorage.getItem("prom_token");
  const role = localStorage.getItem("prom_user_role");

  if (!token) {
    window.location.href = "login.html";
    return false;
  }

  if (role !== "owner") {
    // Redirect candidates to their portal
    window.location.href = "index.html";
    return false;
  }

  // Update header with user name
  const userName = localStorage.getItem("prom_user_name") || "Owner";
  document.getElementById("header-user").textContent = `Hello, ${userName}`;

  return true;
}

// ── Load Owner Listings ───────────────────────────────────────────────────────
async function loadOwnerListings() {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/my-listings`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      throw new Error("Failed to load listings");
    }

    const seats = await res.json();
    renderOwnerListings(seats);
  } catch (err) {
    console.error("Error loading listings:", err);
    showToast("Failed to load listings", "error");
  }
}

// ── Render Owner Listings ─────────────────────────────────────────────────────
function renderOwnerListings(seats) {
  const container = document.getElementById("owner-listings-container");

  if (!seats || seats.length === 0) {
    container.innerHTML = `
      <div style="padding:2rem;text-align:center;color:var(--text-muted)">
        <p style="margin-bottom:1rem">You don't have any listings yet.</p>
        <button class="btn btn-primary" onclick="openTab('page-create-listing')">Create your first listing</button>
      </div>
    `;
    return;
  }

  container.innerHTML = seats
    .map((seat) => {
      const statusBadge = getStatusBadge(seat);
      const actionButtons = getActionButtons(seat);
      const alertBox = getAlertBox(seat);

      return `
      <div class="owner-listing-card">
        <div class="owner-listing-header">
          <div>
            <h3 class="owner-listing-title">${seat.title}</h3>
            <p class="owner-listing-meta">${seat.client_name} · ${seat.work_location}</p>
          </div>
          ${statusBadge}
        </div>

        <div class="owner-listing-stats">
          <div class="stat-item">
            <label>Last updated</label>
            <span>${seat.days_since_update} days ago</span>
          </div>
          <div class="stat-item">
            <label>Expires in</label>
            <span class="${seat.days_until_expiration <= 3 ? "text-danger" : seat.days_until_expiration <= 7 ? "text-warning" : ""}">${
        seat.is_expired ? "Expired" : `${seat.days_until_expiration} days`
      }</span>
          </div>
          <div class="stat-item">
            <label>Profs in play</label>
            <span>${seat.profs_in_play}${
        seat.status_breakdown
          ? ` (P:${seat.status_breakdown.proposed}, S:${seat.status_breakdown.selected}, N:${seat.status_breakdown.not_selected})`
          : ""
      }</span>
          </div>
          <div class="stat-item">
            <label>Listing type</label>
            <span>${seat.seat_type === "real" ? "Actively hiring" : "Formality/compliance"}</span>
          </div>
        </div>

        <div class="owner-listing-actions">
          ${actionButtons}
        </div>

        ${alertBox}
      </div>
    `;
    })
    .join("");
}

// ── Get Status Badge ──────────────────────────────────────────────────────────
function getStatusBadge(seat) {
  if (seat.is_expired) {
    return '<span class="badge" style="background:#ffebee;color:#c62828">Expired</span>';
  }
  if (seat.seat_type === "formal") {
    return '<span class="badge" style="background:#f3e5f5;color:#8e24aa">Formality</span>';
  }
  if (seat.days_until_expiration <= 7) {
    return '<span class="badge" style="background:#fff3e0;color:#f57c00">Expiring soon</span>';
  }
  return '<span class="badge" style="background:#e3f2fd;color:#1976d2">Active</span>';
}

// ── Get Action Buttons ────────────────────────────────────────────────────────
function getActionButtons(seat) {
  if (seat.is_expired) {
    return `
      <button class="btn btn-primary btn-sm" onclick="reactivateListing('${seat.seat_id}')">Reactivate listing</button>
      <button class="btn btn-secondary btn-sm" onclick="editListing('${seat.seat_id}')">Edit listing</button>
      <button class="btn btn-ghost btn-sm text-danger" onclick="deleteListing('${seat.seat_id}')">Delete listing</button>
    `;
  }

  const typeButton =
    seat.seat_type === "real"
      ? `<button class="btn btn-ghost btn-sm" onclick="markAsFormal('${seat.seat_id}')">Mark as formality</button>`
      : `<button class="btn btn-ghost btn-sm" onclick="markAsReal('${seat.seat_id}')">Mark as actively hiring</button>`;

  return `
    <button class="btn btn-primary btn-sm" onclick="confirmListing('${seat.seat_id}')">Confirm still active</button>
    <button class="btn btn-secondary btn-sm" onclick="editListing('${seat.seat_id}')">Edit listing</button>
    ${typeButton}
    <button class="btn btn-ghost btn-sm text-danger" onclick="closeListing('${seat.seat_id}')">Close listing</button>
  `;
}

// ── Get Alert Box ─────────────────────────────────────────────────────────────
function getAlertBox(seat) {
  if (seat.is_expired) {
    return `
      <div class="owner-listing-reminder" style="margin-top:.75rem;padding:.75rem;background:#ffebee;border:1px solid #c62828;border-radius:4px;font-size:12px">
        🔒 <strong>Listing hidden:</strong> This listing expired ${Math.abs(seat.days_until_expiration)} days ago and is no longer visible to candidates. Reactivate to make it public again.
      </div>
    `;
  }

  if (seat.days_until_expiration <= 7) {
    return `
      <div class="owner-listing-reminder" style="margin-top:.75rem;padding:.75rem;background:#fff3e0;border:1px solid #ffa726;border-radius:4px;font-size:12px">
        ⚠️ <strong>Action needed:</strong> This listing will expire in ${seat.days_until_expiration} days. Click "Confirm still active" to extend visibility for 30 days.
      </div>
    `;
  }

  if (seat.seat_type === "formal") {
    return `
      <div class="owner-listing-info" style="margin-top:.75rem;padding:.75rem;background:#f3e5f5;border:1px solid #8e24aa;border-radius:4px;font-size:12px">
        ℹ️ This listing is visible in the "Formality postings" tab. Candidates can still apply but see accurate expectations.
      </div>
    `;
  }

  return "";
}

// ── Listing Actions ───────────────────────────────────────────────────────────
async function confirmListing(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/confirm-listing`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ seat_id: seatId }),
    });

    if (!res.ok) {
      throw new Error("Failed to confirm listing");
    }

    const data = await res.json();
    showToast(data.message, "success");
    loadOwnerListings();
  } catch (err) {
    console.error("Error confirming listing:", err);
    showToast("Failed to confirm listing", "error");
  }
}

async function markAsFormal(seatId) {
  if (!confirm("Mark this listing as a formality/compliance posting? Candidates will see it in a separate tab.")) {
    return;
  }

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/update-listing-type`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ seat_id: seatId, seat_type: "formal" }),
    });

    if (!res.ok) {
      throw new Error("Failed to update listing type");
    }

    const data = await res.json();
    showToast(data.message, "success");
    loadOwnerListings();
  } catch (err) {
    console.error("Error updating listing:", err);
    showToast("Failed to update listing", "error");
  }
}

async function markAsReal(seatId) {
  if (!confirm("Mark this listing as actively hiring?")) {
    return;
  }

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/update-listing-type`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ seat_id: seatId, seat_type: "real" }),
    });

    if (!res.ok) {
      throw new Error("Failed to update listing type");
    }

    const data = await res.json();
    showToast(data.message, "success");
    loadOwnerListings();
  } catch (err) {
    console.error("Error updating listing:", err);
    showToast("Failed to update listing", "error");
  }
}

async function closeListing(seatId) {
  if (!confirm("Close this listing? It will be hidden from candidates.")) {
    return;
  }

  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/close-listing/${seatId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      throw new Error("Failed to close listing");
    }

    const data = await res.json();
    showToast(data.message, "success");
    loadOwnerListings();
  } catch (err) {
    console.error("Error closing listing:", err);
    showToast("Failed to close listing", "error");
  }
}

async function reactivateListing(seatId) {
  try {
    const token = localStorage.getItem("prom_token");
    const res = await fetch(`${API_BASE}/owner/reactivate-listing/${seatId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      throw new Error("Failed to reactivate listing");
    }

    const data = await res.json();
    showToast(data.message, "success");
    loadOwnerListings();
  } catch (err) {
    console.error("Error reactivating listing:", err);
    showToast("Failed to reactivate listing", "error");
  }
}

function editListing(seatId) {
  showToast("Edit functionality coming soon", "info");
}

function deleteListing(seatId) {
  if (!confirm("Permanently delete this listing? This cannot be undone.")) {
    return;
  }
  showToast("Delete functionality coming soon", "info");
}

// ── Agent: Expiration Check ───────────────────────────────────────────────────
async function runExpirationCheck() {
  const btn = document.getElementById("btn-expiration-check");
  const output = document.getElementById("expiration-output");

  btn.disabled = true;
  btn.textContent = "Checking...";
  output.innerHTML = '<span class="spinner"></span>';

  try {
    const token = localStorage.getItem("prom_token");

    // First, get owner's listings
    const listingsRes = await fetch(`${API_BASE}/owner/my-listings`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!listingsRes.ok) {
      throw new Error("Failed to load listings");
    }

    const seats = await listingsRes.json();

    // Run expiration check
    const res = await fetch(`${API_BASE}/agents/expiration-check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(seats),
    });

    if (!res.ok) {
      throw new Error("Expiration check failed");
    }

    const result = await res.json();

    // Render results
    output.innerHTML = `
      <div style="padding:.75rem;background:var(--bg-secondary);border-radius:4px">
        <p style="font-weight:600;margin-bottom:.75rem">${result.summary}</p>
        ${
          result.data.recommendations.length > 0
            ? `
          <div style="margin-top:.75rem">
            ${result.data.recommendations
              .map(
                (rec) => `
              <div style="padding:.5rem;margin-bottom:.5rem;background:var(--card-bg);border-left:3px solid ${
                rec.urgency === "high" ? "var(--ibm-red)" : "var(--ibm-orange)"
              };border-radius:2px">
                <div style="font-weight:600;font-size:13px">${rec.listing}</div>
                <div style="font-size:12px;color:var(--text-muted);margin-top:.25rem">${rec.message}</div>
              </div>
            `
              )
              .join("")}
          </div>
        `
            : ""
        }
      </div>
    `;
  } catch (err) {
    console.error("Error running expiration check:", err);
    output.innerHTML = `<p class="text-danger">Failed to run expiration check</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Check all my listings for expiration";
  }
}

// ── Agent: Mismatch Check ─────────────────────────────────────────────────────
async function runMismatchCheck() {
  const btn = document.getElementById("btn-mismatch-check");
  const output = document.getElementById("mismatch-output");

  btn.disabled = true;
  btn.textContent = "Checking...";
  output.innerHTML = '<span class="spinner"></span>';

  try {
    const token = localStorage.getItem("prom_token");

    // Get owner's listings
    const listingsRes = await fetch(`${API_BASE}/owner/my-listings`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!listingsRes.ok) {
      throw new Error("Failed to load listings");
    }

    const seats = await listingsRes.json();

    // Run mismatch check for each listing
    const mismatchPromises = seats.map((seat) =>
      fetch(`${API_BASE}/agents/mismatch-check`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ seat_id: seat.seat_id }),
      }).then((res) => res.json())
    );

    const results = await Promise.all(mismatchPromises);
    const mismatches = results.filter((r) => r.mismatch_detected);

    // Render results
    if (mismatches.length === 0) {
      output.innerHTML = `
        <div style="padding:.75rem;background:var(--bg-secondary);border-radius:4px">
          <p style="color:var(--ibm-green)">✅ No mismatches detected. All listings appear accurate.</p>
        </div>
      `;
    } else {
      output.innerHTML = `
        <div style="padding:.75rem;background:var(--bg-secondary);border-radius:4px">
          <p style="font-weight:600;margin-bottom:.75rem">⚠️ ${mismatches.length} mismatch(es) detected</p>
          <div style="margin-top:.75rem">
            ${mismatches
              .map((m) => {
                const seat = seats.find((s) => s.seat_id === m.seat_id);
                return `
                <div style="padding:.5rem;margin-bottom:.5rem;background:var(--card-bg);border-left:3px solid var(--ibm-red);border-radius:2px">
                  <div style="font-weight:600;font-size:13px">${seat?.title || m.seat_id}</div>
                  <div style="font-size:12px;color:var(--text-muted);margin-top:.25rem">${m.reason}</div>
                  <div style="font-size:12px;color:var(--ibm-blue);margin-top:.5rem">${m.ai_recommendation_note}</div>
                </div>
              `;
              })
              .join("")}
          </div>
        </div>
      `;
    }
  } catch (err) {
    console.error("Error running mismatch check:", err);
    output.innerHTML = `<p class="text-danger">Failed to run mismatch check</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Check for filled-but-posted listings";
  }
}

// ── Create Listing ────────────────────────────────────────────────────────────
async function createListing(event) {
  event.preventDefault();
  showToast("Create listing functionality coming soon", "info");
}

// ── Filter Owner Listings ─────────────────────────────────────────────────────
function filterOwnerListings() {
  showToast("Filter functionality coming soon", "info");
}

// ── Initialize ────────────────────────────────────────────────────────────────
if (checkOwnerAuth()) {
  loadOwnerListings();
}
