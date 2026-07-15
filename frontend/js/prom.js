/**
 * prom.js — ProM Modernized frontend
 * Handles tab navigation, API calls to the FastAPI backend,
 * and rendering all three pages including agentic feature panels.
 */

const API = "http://127.0.0.1:8000/api";

// Get current user from session
function getCurrentUserId() {
  return localStorage.getItem("prom_user_id") || null;
}

function getCurrentUserName() {
  return localStorage.getItem("prom_user_name") || "User";
}

function getAuthToken() {
  return localStorage.getItem("prom_token") || null;
}

const CURRENT_USER_ID = getCurrentUserId();

// ── Toasts ────────────────────────────────────────────────────────────────────
function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────
async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Authentication ────────────────────────────────────────────────────────────
function checkAuth() {
  if (!CURRENT_USER_ID || !getAuthToken()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function logout() {
  localStorage.removeItem("prom_token");
  localStorage.removeItem("prom_user_id");
  localStorage.removeItem("prom_user_name");
  window.location.href = "login.html";
}

function updateUserDisplay() {
  const userName = getCurrentUserName();
  const headerUser = document.getElementById("header-user");
  if (headerUser) {
    const firstName = userName.split("/")[0].split(" ")[0];
    headerUser.textContent = `Hello, ${firstName}`;
  }
}

// ── Tab Navigation ────────────────────────────────────────────────────────────
function openTab(target) {
  const btn = document.querySelector(`.tab-btn[data-tab="${target}"]`);
  if (!btn) return;
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById(target).classList.add("active");
}

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => openTab(btn.dataset.tab));
  });
}

// ── Section collapse ──────────────────────────────────────────────────────────
function initCollapse() {
  document.querySelectorAll(".section-header").forEach((header) => {
    header.addEventListener("click", () => {
      header.classList.toggle("collapsed");
      const body = header.nextElementSibling;
      body.style.display = header.classList.contains("collapsed") ? "none" : "";
    });
  });
}

function setActiveCVSection(targetId) {
  const section = document.getElementById(targetId);
  if (!section) return null;

  document.querySelectorAll(".cv-nav-item[data-cv-target]").forEach((item) => {
    item.classList.toggle("active", item.dataset.cvTarget === targetId);
  });
  document.querySelectorAll(".cv-builder-section").forEach((item) => {
    item.classList.toggle("is-active", item.id === targetId);
  });

  return section;
}

function initCVBuilderNav() {
  document.querySelectorAll(".cv-nav-item[data-cv-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const section = setActiveCVSection(button.dataset.cvTarget);
      if (!section) return;
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function createInlineEditor(section) {
  const existing = section.querySelector(".cv-inline-editor");
  if (existing) return existing;

  const content = section.querySelector(".cv-editable-content, .cv-empty-state");
  if (!content) return null;

  const editor = document.createElement("textarea");
  editor.className = "cv-inline-editor";
  editor.value = content.classList.contains("cv-empty-state")
    ? ""
    : content.innerText.replace(/\n{2,}/g, "\n").trim();

  content.hidden = true;
  content.insertAdjacentElement("afterend", editor);
  return editor;
}

function initCVActionButtons() {
  document.querySelectorAll(".cv-action-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const section = button.closest(".cv-builder-section");
      if (!section) return;

      setActiveCVSection(section.id);
      const primaryEditor = section.querySelector("#cv-editor");
      const label = button.dataset.sectionLabel || section.querySelector("h2")?.textContent || "section";

      if (primaryEditor) {
        primaryEditor.focus();
        primaryEditor.scrollIntoView({ behavior: "smooth", block: "center" });
        showToast(`Editing ${label.toLowerCase()}`, "info");
        return;
      }

      const inlineEditor = createInlineEditor(section);
      if (!inlineEditor) return;

      inlineEditor.focus();
      inlineEditor.scrollIntoView({ behavior: "smooth", block: "center" });
      button.textContent = "Edit";
      button.classList.remove("btn-secondary");
      button.classList.add("btn-ghost");
      showToast(`Editing ${label.toLowerCase()}`, "info");
    });
  });
}

// ── Seat card expand ──────────────────────────────────────────────────────────
function initSeatCards() {
  document.addEventListener("click", (e) => {
    const header = e.target.closest(".seat-card-header");
    if (!header) return;
    header.parentElement.classList.toggle("expanded");
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// PAGE: My Profile
// ══════════════════════════════════════════════════════════════════════════════
async function loadProfile() {
  try {
    const profile = await apiGet(`/profile/${CURRENT_USER_ID}`);
    document.getElementById("prof-id").textContent = profile.professional_id;
    document.getElementById("prof-name").textContent = profile.name;
    document.getElementById("prof-avail").textContent = profile.availability_date;
    document.getElementById("prof-band").textContent = profile.band || "—";
    document.getElementById("prof-location").textContent = profile.location || "—";
    document.getElementById("prof-skills").textContent =
      profile.skills?.join(", ") || "—";
  } catch {
    showToast("Could not load profile — backend may be offline", "error");
  }
}

// ── Agent #1: Stale check on profile's open seats ─────────────────────────────
async function runStaleCheckForProfile() {
  const btn = document.getElementById("btn-stale-check");
  const output = document.getElementById("stale-output");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Checking...';
  output.innerHTML = "";

  try {
    // Run stale check on first available seat as demo; real impl iterates all seats
    const result = await apiPost("/agents/stale-check", {
      seat_id: "SEAT-001",
      days_threshold: 30,
    });
    if (result.is_stale) {
      output.innerHTML = `
        <div class="stale-banner">
          ⚠ Seat <strong>SEAT-001</strong> is stale (${result.days_since_update} days). 
          Nudge drafted below.
        </div>
        <div class="ai-panel">
          <div class="ai-panel-header"><span class="ai-icon">🤖</span> Draft nudge to owner</div>
          <div class="ai-panel-body">
            <textarea id="stale-nudge-text">${result.nudge_draft}</textarea>
            <div class="ai-panel-actions">
              <button class="btn btn-primary btn-sm" onclick="sendNudge()">Send via Slack / Email</button>
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('stale-output').innerHTML=''">Dismiss</button>
            </div>
          </div>
        </div>`;
      showToast("Stale listing detected — nudge drafted", "info");
    } else {
      output.innerHTML = `<div class="flex-row"><span style="color:var(--ibm-green)">✓</span> No stale seats found.</div>`;
    }
  } catch (err) {
    showToast("Stale check failed: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Check for stale listings";
  }
}

function sendNudge() {
  const text = document.getElementById("stale-nudge-text")?.value;
  // TODO: integrate with Slack/email API when adding real agent
  showToast("Nudge sent to seat owner", "success");
}

function getPersonalStatusClass(value) {
  const normalized = value.toLowerCase();
  if (normalized.includes("interview scheduled")) return "personal-status-interview";
  if (normalized.includes("interview completed")) return "personal-status-complete";
  if (normalized.includes("follow-up")) return "personal-status-follow-up";
  if (normalized.includes("no response")) return "personal-status-no-response";
  return "personal-status-pending";
}

function updatePersonalStatusLabel(select, labelId) {
  const label = document.getElementById(labelId);
  if (!label) return;
  label.textContent = select.value;
  label.className = `personal-status-pill ${getPersonalStatusClass(select.value)}`;
}

// ── Agent #7: Recommendations for current user ────────────────────────────────
async function loadRecommendations() {
  const container = document.getElementById("recs-container");
  container.innerHTML = '<span class="spinner"></span>';
  try {
    const result = await apiPost("/agents/recommendations", {
      professional_id: CURRENT_USER_ID,
      mode: "candidate",
    });
    if (!result.recommendations.length) {
      container.innerHTML = "<p class='text-muted'>No recommendations available.</p>";
      return;
    }
    container.innerHTML = `
      <p class="text-sm text-muted" style="margin-bottom:.75rem">${result.reasoning}</p>
      <ul class="rec-list">
        ${result.recommendations
          .map(
            (r) => `
          <li class="rec-item">
            <div>
              <div style="font-weight:600;font-size:13px">${r.title || r.name || r.professional_id}</div>
              <div class="rec-reason">${r.reason}</div>
            </div>
            <div class="rec-score">${Math.round((r.match_score || 0) * 100)}% match</div>
          </li>`
          )
          .join("")}
      </ul>`;
  } catch {
    container.innerHTML = "<p class='text-muted text-sm'>Could not load recommendations.</p>";
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// PAGE: Find an Open Seat
// ══════════════════════════════════════════════════════════════════════════════
let allSeats = [];
let currentPage = 1;
let currentPerPage = 30;
let currentQuery = "";

async function loadSeats(page = 1, perPage = 30, query = "") {
  const tableBody = document.getElementById("seats-table-body");
  const resultsMeta = document.getElementById("results-meta");
  tableBody.innerHTML = '<tr><td colspan="12" style="padding:2rem;text-align:center"><span class="spinner"></span></td></tr>';

  try {
    const params = new URLSearchParams({ page, per_page: perPage });
    if (query) params.set("query", query);
    const data = await apiGet(`/seats/?${params}`);
    allSeats = data.seats;

    document.getElementById("matching-count").innerHTML =
      `Number of matching positions still needed: <strong>${data.total}</strong>`;

    resultsMeta.innerHTML = `
      Results ${(page - 1) * perPage + 1}–${Math.min(page * perPage, data.total)} of ${data.total}
      &nbsp;|&nbsp; Per page:
      <span class="per-page-links">
        <a href="#" onclick="changePerPage(10)" class="${perPage === 10 ? "active" : ""}">10</a>
        <a href="#" onclick="changePerPage(30)" class="${perPage === 30 ? "active" : ""}">30</a>
        <a href="#" onclick="changePerPage(50)" class="${perPage === 50 ? "active" : ""}">50</a>
      </span>`;

    tableBody.innerHTML = data.seats.map(renderSeatRow).join("");
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="12" style="color:var(--ibm-red);padding:1rem">Could not load seats — ${err.message}</td></tr>`;
  }
}

function renderSeatRow(seat) {
  // Priority order for row highlighting:
  // 1. Stale (highest priority - warning)
  // 2. Applied (user already applied)
  // 3. Not available (position filled/closed)
  // 4. Available (open for applications)
  let rowClass = '';
  if (seat.is_stale) {
    rowClass = 'stale-row';
  } else if (seat.has_applied) {
    rowClass = 'applied-row';
  } else if (!seat.is_available) {
    rowClass = 'unavailable-row';
  } else if (seat.is_available && !seat.has_applied && !seat.is_stale) {
    rowClass = 'available-row';
  }

  // Build status breakdown display like: 9 ( P 4 S 5 )
  let profsDisplay = seat.profs_in_play.toString();
  if (seat.status_breakdown) {
    const parts = [];
    if (seat.status_breakdown.proposed > 0) {
      parts.push(`<span class="badge badge-P">P</span> ${seat.status_breakdown.proposed}`);
    }
    if (seat.status_breakdown.selected > 0) {
      parts.push(`<span class="badge badge-S">S</span> ${seat.status_breakdown.selected}`);
    }
    if (seat.status_breakdown.not_selected > 0) {
      parts.push(`<span class="badge badge-N">N</span> ${seat.status_breakdown.not_selected}`);
    }
    if (seat.status_breakdown.withdrawn > 0) {
      parts.push(`<span class="badge badge-W">W</span> ${seat.status_breakdown.withdrawn}`);
    }
    if (parts.length > 0) {
      profsDisplay = `${seat.profs_in_play} ( ${parts.join(' ')} )`;
    }
  }

  // Format start date
  const startDate = seat.start_date ? new Date(seat.start_date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }) : '—';

  // Format clearance
  const clearance = seat.clearance_needed || 'None';

  return `
    <tr class="${rowClass}" data-seat-id="${seat.seat_id}">
      <td><input type="checkbox" class="seat-checkbox" value="${seat.seat_id}" /></td>
      <td><a href="#" onclick="expandSeatDetails('${seat.seat_id}'); return false;">${seat.title}</a></td>
      <td>${seat.client_name}</td>
      <td style="text-align:center;font-weight:600;">${seat.positions_still_needed}</td>
      <td class="profs-in-play-cell">${profsDisplay}</td>
      <td style="white-space:nowrap;">${startDate}</td>
      <td>${clearance}</td>
      <td>${seat.owner_notes_id}</td>
      <td>${seat.service}</td>
      <td style="text-align:center;">${seat.requested_band_high}</td>
      <td style="text-align:center;">${seat.requested_band_low}</td>
      <td>${seat.contract_owning_country}</td>
    </tr>`;
}

function expandSeatDetails(seatId) {
  // Navigate to detail page
  window.location.href = `seat-detail.html?id=${seatId}`;
  // TODO: Implement detailed view
}

function toggleSelectAll() {
  const selectAll = document.getElementById("select-all-seats");
  const checkboxes = document.querySelectorAll(".seat-checkbox");
  checkboxes.forEach(cb => cb.checked = selectAll.checked);
}

function toggleColumnManager() {
  showToast("Column manager coming soon", "info");
  // TODO: Implement column visibility manager
}

function renderSeatCard(seat) {
  const flags = [];
  if (seat.is_stale) flags.push(`<span class="status-pill pill-stale">Stale</span>`);
  if (seat.mismatch_flag) flags.push(`<span class="status-pill pill-mismatch">Possible mismatch</span>`);
  if (seat.seat_type === "formal") flags.push(`<span class="status-pill pill-formal">Formal</span>`);
  if (seat.seat_type === "real") flags.push(`<span class="status-pill pill-real">Real opening</span>`);

  const statusBadge = seat.candidate_status
    ? `<span class="badge badge-${seat.candidate_status}" title="Candidate status">${seat.candidate_status}</span>`
    : "";

  const mismatchBanner = seat.mismatch_flag
    ? `<div class="mismatch-banner">⚠ ${seat.ai_recommendation_note || "Possible internal fill detected."}</div>`
    : "";

  return `
    <div class="seat-card" data-seat-id="${seat.seat_id}">
      <div class="seat-card-header">
        <div>
          <div class="seat-card-title">${seat.title}</div>
          <div class="seat-card-client">${seat.client_name}</div>
        </div>
        <div class="seat-card-flags">
          ${statusBadge}
          ${flags.join("")}
          <span class="text-sm text-muted">${seat.profs_in_play} in play</span>
        </div>
      </div>
      <div class="seat-card-body">
        ${mismatchBanner}
        <div class="seat-detail-grid">
          <div class="seat-detail-item"><label>Owner</label><span>${seat.owner_notes_id}</span></div>
          <div class="seat-detail-item"><label>Service</label><span>${seat.service}</span></div>
          <div class="seat-detail-item"><label>Band</label><span>${seat.requested_band_low}–${seat.requested_band_high}</span></div>
          <div class="seat-detail-item"><label>Location</label><span>${seat.work_location}</span></div>
          <div class="seat-detail-item"><label>Remote</label><span>${seat.work_remotely ? "Yes" : "No"}</span></div>
          <div class="seat-detail-item"><label>Sector</label><span>${seat.sector}</span></div>
          <div class="seat-detail-item"><label>Country</label><span>${seat.contract_owning_country}</span></div>
          <div class="seat-detail-item"><label>Last updated</label><span>${seat.days_since_update}d ago</span></div>
        </div>
        <div class="seat-card-actions">
          <button class="btn btn-primary btn-sm" onclick="openOutreachPanel('${seat.seat_id}')">✉ Draft outreach email</button>
          <button class="btn btn-secondary btn-sm" onclick="openCVTailorPanel('${seat.seat_id}')">📄 Tailor my CV</button>
          <button class="btn btn-ghost btn-sm" onclick="runMismatchCheck('${seat.seat_id}')">🔍 Check mismatch</button>
        </div>
        <div id="agent-panel-${seat.seat_id}"></div>
      </div>
    </div>`;
}

function changePerPage(n) {
  currentPerPage = n;
  loadSeats(1, n, currentQuery);
}

function searchSeats() {
  currentQuery = document.getElementById("search-input").value.trim();
  loadSeats(1, currentPerPage, currentQuery);
}

// ── Agent #5: Outreach email drafter ─────────────────────────────────────────
async function openOutreachPanel(seatId) {
  const panel = document.getElementById(`agent-panel-${seatId}`);
  panel.innerHTML = '<div style="padding:.5rem"><span class="spinner"></span> Drafting email...</div>';

  try {
    const result = await apiPost("/agents/outreach-draft", {
      seat_id: seatId,
      candidate_professional_id: CURRENT_USER_ID,
    });
    panel.innerHTML = `
      <div class="ai-panel">
        <div class="ai-panel-header"><span class="ai-icon">✉</span> AI-drafted outreach email — edit before sending</div>
        <div class="ai-panel-body">
          <div class="email-subject">Subject: ${result.subject}</div>
          <textarea id="email-body-${seatId}">${result.body}</textarea>
          <div class="ai-panel-actions">
            <button class="btn btn-primary btn-sm" onclick="sendOutreach('${seatId}')">Send via Outlook</button>
            <button class="btn btn-secondary btn-sm" onclick="document.getElementById('agent-panel-${seatId}').innerHTML=''">Cancel</button>
          </div>
        </div>
      </div>`;
  } catch (err) {
    panel.innerHTML = `<p style="color:var(--ibm-red);font-size:13px">Draft failed: ${err.message}</p>`;
  }
}

function sendOutreach(seatId) {
  // TODO: integrate with Outlook Graph API when adding real agent
  showToast("Email sent via Outlook", "success");
  document.getElementById(`agent-panel-${seatId}`).innerHTML = "";
}

// ── Agent #8: CV tailor ───────────────────────────────────────────────────────
async function openCVTailorPanel(seatId) {
  const panel = document.getElementById(`agent-panel-${seatId}`);
  const editor = document.getElementById("cv-editor");
  panel.innerHTML = '<div style="padding:.5rem"><span class="spinner"></span> Tailoring CV...</div>';

  try {
    const result = await apiPost("/agents/cv-tailor", {
      seat_id: seatId,
      professional_id: CURRENT_USER_ID,
    });
    const changeItems = result.changes_summary
      .map((c) => `<li>${c}</li>`)
      .join("");
    if (editor) {
      editor.value = result.tailored_cv_text;
      updateCVTimestamp();
    }
    panel.innerHTML = `
      <div class="ai-panel">
        <div class="ai-panel-header"><span class="ai-icon">📄</span> Tailored CV applied in ProM editor</div>
        <div class="ai-panel-body">
          <p>Your role-specific CV draft is now loaded into the native ProM editor above.</p>
          <ul class="cv-changes">${changeItems}</ul>
          <div class="ai-panel-actions">
            <button class="btn btn-primary btn-sm" onclick="focusCVEditor()">Review in editor</button>
            <button class="btn btn-secondary btn-sm" onclick="saveCVEdits()">Save draft</button>
            <button class="btn btn-secondary btn-sm" onclick="document.getElementById('agent-panel-${seatId}').innerHTML=''">Dismiss</button>
          </div>
        </div>
      </div>`;
  } catch (err) {
    panel.innerHTML = `<p style="color:var(--ibm-red);font-size:13px">CV tailor failed: ${err.message}</p>`;
  }
}

function updateCVTimestamp() {
  showToast("CV updated in ProM", "info");
}

function focusCVEditor() {
  const editor = document.getElementById("cv-editor");
  if (!editor) return;
  editor.focus();
  editor.scrollIntoView({ behavior: "smooth", block: "center" });
}

function saveCVEdits() {
  updateCVTimestamp();
  showToast("CV changes saved in ProM", "success");
}

function enhanceCVSummary() {
  const editor = document.getElementById("cv-editor");
  if (!editor) return;

  const text = editor.value.trim();
  if (!text) {
    showToast("Add some CV content before enhancing it", "info");
    return;
  }

  if (!text.includes("Results-focused")) {
    editor.value = `Results-focused ${text.charAt(0).toLowerCase()}${text.slice(1)}`;
  }
  updateCVTimestamp();
  showToast("CV summary enhanced in ProM", "success");
}

// ── Agent #2: Mismatch check ──────────────────────────────────────────────────
async function runMismatchCheck(seatId) {
  const panel = document.getElementById(`agent-panel-${seatId}`);
  panel.innerHTML = '<div style="padding:.5rem"><span class="spinner"></span> Checking...</div>';

  try {
    const result = await apiPost("/agents/mismatch-check", { seat_id: seatId });
    if (result.mismatch_detected) {
      panel.innerHTML = `
        <div class="ai-panel" style="border-color:var(--ibm-red);background:var(--ibm-red-light)">
          <div class="ai-panel-header" style="color:var(--ibm-red)"><span class="ai-icon">⚠</span> Mismatch Detected</div>
          <div class="ai-panel-body">
            <p>${result.reason}</p>
            <p style="margin-top:.5rem;font-style:italic">${result.ai_recommendation_note}</p>
          </div>
        </div>`;
    } else {
      panel.innerHTML = `<div class="flex-row" style="padding:.5rem"><span style="color:var(--ibm-green)">✓</span> No mismatch detected for this seat.</div>`;
      setTimeout(() => (panel.innerHTML = ""), 3000);
    }
  } catch (err) {
    panel.innerHTML = `<p style="color:var(--ibm-red);font-size:13px">Check failed: ${err.message}</p>`;
  }
}

// ── Find matching seats for me ────────────────────────────────────────────────
async function findMatchingSeats() {
  currentQuery = "";
  document.getElementById("search-input").value = "";
  await loadSeats(1, currentPerPage, "");
  showToast("Showing all available seats — AI match scoring coming with watsonx integration", "info");
}

// ── Apply category filters ────────────────────────────────────────────────────
function applyFilters() {
  const checkboxes = document.querySelectorAll(".filter-checkbox:checked");
  const filters = {
    owner: [],
    client: [],
    location: [],
    remote: [],
    sector: []
  };

  checkboxes.forEach(cb => {
    const filterType = cb.dataset.filter;
    filters[filterType].push(cb.value);
  });

  // Build query string for filters
  let filterQuery = "";
  if (filters.owner.length) filterQuery += filters.owner.join(" OR ");
  if (filters.client.length) filterQuery += (filterQuery ? " OR " : "") + filters.client.join(" OR ");
  if (filters.location.length) filterQuery += (filterQuery ? " OR " : "") + filters.location.join(" OR ");
  if (filters.sector.length) filterQuery += (filterQuery ? " OR " : "") + filters.sector.join(" OR ");

  // For remote filter, just use the first value if any
  const remoteFilter = filters.remote.length ? filters.remote[0] : null;

  currentQuery = filterQuery;
  loadSeats(1, currentPerPage, filterQuery);
  showToast(`Applied ${checkboxes.length} filter(s)`, "info");
}

// ══════════════════════════════════════════════════════════════════════════════
// Init
// ══════════════════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  // Check authentication first
  if (!checkAuth()) {
    return;
  }

  updateUserDisplay();

  initTabs();
  initCollapse();
  initCVBuilderNav();
  initCVActionButtons();
  initSeatCards();

  // Load profile data
  loadProfile();
  loadRecommendations();

  // Load seats when Find tab is activated
  document.querySelector('[data-tab="page-find"]').addEventListener("click", () => {
    if (!allSeats.length) loadSeats();
  });

  // Search on Enter
  document.getElementById("search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchSeats();
  });
});
