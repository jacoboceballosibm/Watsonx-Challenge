/**
 * prom.js — ProM Modernized frontend
 * Handles tab navigation, API calls to the FastAPI backend,
 * and rendering all three pages including agentic feature panels.
 *
 * NOTE: API base URL is now defined in config.js
 */

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

const CV_STATE = {
  activeCvId: null,
  activeCv: null,
  repository: [],
  agentDraft: null,
  isTailoring: false,
};

const RESUME_SECTION_LABELS = {
  work_experience: "Work experience",
  ibm_assignment_history: "IBM assignment history",
  additional_client_history: "Additional client history",
  industry_experience: "Industry experience",
  education: "Education",
  languages: "Languages",
  publications: "Publications",
  memberships: "Memberships",
  additional_information: "Additional information",
};

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
async function parseApiError(res) {
  try {
    const body = await res.json();
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
      : body.detail;
    return detail || `HTTP ${res.status}`;
  } catch {
    return `HTTP ${res.status}`;
  }
}

async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

async function apiPatch(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
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
  localStorage.removeItem("prom_professional_id");
  localStorage.removeItem("prom_user_role");
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
function defaultContactFromProfile(profile) {
  const displayName = profile.name?.split("/")?.[0] || profile.name || "";
  return {
    name: displayName,
    title: profile.band ? `IBM Band ${profile.band} Professional` : "IBM Professional",
    phone: "",
    email: profile.w3_link || "",
    ...(profile.cv_contact || {}),
  };
}

function renderCVContact(profile) {
  const contact = defaultContactFromProfile(profile);
  const contactBlock = document.querySelector("#cv-contact-information .cv-contact-block");
  if (!contactBlock) return;

  const inlineEditor = document.querySelector("#cv-contact-information .cv-inline-editor");
  if (inlineEditor) inlineEditor.remove();
  contactBlock.hidden = false;

  document.getElementById("cv-contact-name").textContent = contact.name || "";
  document.getElementById("cv-contact-title").textContent = contact.title || "";
  document.getElementById("cv-contact-phone").textContent = contact.phone || "";
  document.getElementById("cv-contact-email").textContent = contact.email || "";
}

function collectCVContact() {
  const inlineEditor = document.querySelector("#cv-contact-information .cv-inline-editor");
  const lines = inlineEditor
    ? inlineEditor.value.split(/\r?\n/)
    : [
        document.getElementById("cv-contact-name")?.textContent,
        document.getElementById("cv-contact-title")?.textContent,
        document.getElementById("cv-contact-phone")?.textContent,
        document.getElementById("cv-contact-email")?.textContent,
      ];

  const clean = lines.map((line) => (line || "").trim()).filter(Boolean);
  return {
    name: clean[0] || "",
    title: clean[1] || "",
    phone: clean[2] || "",
    email: clean[3] || "",
  };
}

function textToLines(text) {
  return (text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function escapeHTML(value) {
  return (value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderPlainCVContent(content, text, emptyText) {
  const lines = textToLines(text);
  content.replaceChildren();

  if (!lines.length) {
    content.textContent = emptyText;
    content.classList.add("text-muted", "cv-empty-state");
    content.hidden = false;
    return;
  }

  content.classList.remove("text-muted", "cv-empty-state");
  lines.forEach((line, index) => {
    const element = document.createElement(index === 0 ? "h3" : "p");
    if (index === 1) element.className = "cv-entry-meta";
    element.textContent = line;
    content.appendChild(element);
  });
  content.hidden = false;
}

function renderCVSections(profile) {
  const sections = profile.cv_sections || {};
  document.querySelectorAll("[data-cv-section-key]").forEach((content) => {
    const key = content.dataset.cvSectionKey;
    const section = content.closest(".cv-builder-section");
    const inlineEditor = section?.querySelector(".cv-inline-editor");
    if (inlineEditor) inlineEditor.remove();

    const fallback = content.dataset.emptyText || content.textContent.trim();
    content.dataset.emptyText = fallback;
    renderPlainCVContent(content, sections[key] || "", fallback);
  });
}

function collectCVSections() {
  const sections = {};
  document.querySelectorAll("[data-cv-section-key]").forEach((content) => {
    const key = content.dataset.cvSectionKey;
    const section = content.closest(".cv-builder-section");
    const inlineEditor = section?.querySelector(".cv-inline-editor");
    const value = inlineEditor
      ? inlineEditor.value.trim()
      : content.innerText.replace(/\n{2,}/g, "\n").trim();

    const emptyText = content.dataset.emptyText || "";
    sections[key] = value === emptyText ? "" : value;
  });
  return sections;
}

function collectCurrentCVPayload() {
  const editor = document.getElementById("cv-editor");
  const skillsEditor = document.getElementById("cv-skills-editor");
  const skills = skillsEditor
    ? skillsEditor.value
        .split(/\r?\n|,/)
        .map((skill) => skill.trim())
        .filter(Boolean)
    : [];

  return {
    cv_contact: collectCVContact(),
    cv_overview: editor?.value.trim() || "",
    skills,
    cv_sections: collectCVSections(),
  };
}

function appendText(parent, tagName, text, className) {
  if (!text) return null;
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  parent.appendChild(element);
  return element;
}

function previewDataFromCurrentEditor() {
  const payload = collectCurrentCVPayload();
  return {
    name: CV_STATE.activeCv?.name || "Current CV",
    target_role: CV_STATE.activeCv?.target_role || null,
    ...payload,
  };
}

function renderResumeSection(container, title, text) {
  if (!text?.trim()) return;
  const section = document.createElement("section");
  section.className = "resume-preview-section";
  appendText(section, "h3", title);

  const lines = textToLines(text);
  const entry = document.createElement("div");
  entry.className = "resume-preview-entry";
  appendText(entry, "p", lines[0] || text, "resume-preview-entry-title");
  if (lines[1]) appendText(entry, "p", lines[1], "resume-preview-entry-meta");
  if (lines.length > 2) {
    appendText(entry, "p", lines.slice(2).join("\n"), "resume-preview-entry-body");
  }
  section.appendChild(entry);
  container.appendChild(section);
}

function renderResumePreview(cv = null) {
  const data = cv || previewDataFromCurrentEditor();
  const contact = data.cv_contact || {};
  const name = contact.name || data.name || "Resume";

  document.getElementById("resume-preview-name").textContent = name;
  document.getElementById("resume-preview-title").textContent =
    contact.title || data.target_role || "";

  const contactContainer = document.getElementById("resume-preview-contact");
  contactContainer.replaceChildren();
  [contact.phone, contact.email].filter(Boolean).forEach((item) => {
    appendText(contactContainer, "span", item);
  });

  document.getElementById("resume-preview-overview").textContent =
    data.cv_overview || "";

  const skillsList = document.getElementById("resume-preview-skills");
  skillsList.replaceChildren();
  (data.skills || []).forEach((skill) => appendText(skillsList, "li", skill));

  const sectionsContainer = document.getElementById("resume-preview-sections");
  sectionsContainer.replaceChildren();
  Object.entries(RESUME_SECTION_LABELS).forEach(([key, label]) => {
    renderResumeSection(sectionsContainer, label, data.cv_sections?.[key] || "");
  });
}

function toggleResumePreview() {
  const card = document.querySelector(".cv-preview-card");
  const button = document.getElementById("resume-preview-toggle");
  if (!card || !button) return;

  const isMinimized = card.classList.toggle("is-minimized");
  button.textContent = isMinimized ? "Expand" : "Minimize";
  button.setAttribute("aria-expanded", String(!isMinimized));
}

function renderActiveCVMeta(cv) {
  document.getElementById("active-cv-name").textContent = cv?.name || "Unsaved CV";
  document.getElementById("active-cv-target").textContent = cv?.target_role || "No target role";
}

function renderCVDocument(cv) {
  CV_STATE.activeCvId = cv.cv_id;
  CV_STATE.activeCv = cv;

  const cvEditor = document.getElementById("cv-editor");
  if (cvEditor) cvEditor.value = cv.cv_overview || "";

  const skillsEditor = document.getElementById("cv-skills-editor");
  if (skillsEditor) skillsEditor.value = cv.skills?.join("\n") || "";

  renderCVContact({
    name: cv.cv_contact?.name || cv.name,
    cv_contact: cv.cv_contact,
  });
  renderCVSections({ cv_sections: cv.cv_sections || {} });
  renderActiveCVMeta(cv);
  renderResumePreview(cv);
}

function renderCVRepository() {
  const list = document.getElementById("cv-repository-list");
  if (!list) return;

  if (!CV_STATE.repository.length) {
    list.innerHTML = "<span class='text-muted text-sm'>No saved CVs yet.</span>";
    renderActiveCVMeta(null);
    return;
  }

  list.innerHTML = "";
  CV_STATE.repository.forEach((cv) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `cv-repository-item ${cv.cv_id === CV_STATE.activeCvId ? "active" : ""}`;
    button.dataset.cvId = cv.cv_id;

    const name = document.createElement("strong");
    name.textContent = cv.name;
    const meta = document.createElement("span");
    meta.textContent = cv.target_role || (cv.is_default ? "Default CV" : "General CV");

    button.append(name, meta);
    button.addEventListener("click", () => selectCV(cv.cv_id));
    list.appendChild(button);
  });
}

async function loadCVRepository() {
  if (!CURRENT_USER_ID) return;
  try {
    const response = await apiGet(`/cvs?professional_id=${encodeURIComponent(CURRENT_USER_ID)}`);
    CV_STATE.repository = response.cvs || [];
    const active = CV_STATE.repository.find((cv) => cv.is_default) || CV_STATE.repository[0];
    if (active) renderCVDocument(active);
    renderCVRepository();
  } catch (err) {
    document.getElementById("cv-repository-list").innerHTML =
      "<span class='text-muted text-sm'>Could not load CV repository.</span>";
  }
}

function selectCV(cvId) {
  const cv = CV_STATE.repository.find((item) => item.cv_id === cvId);
  if (!cv) return;
  renderCVDocument(cv);
  renderCVRepository();
  showToast(`Opened ${cv.name}`, "info");
}

async function saveActiveCVDocument() {
  if (!CV_STATE.activeCvId) return null;
  const payload = collectCurrentCVPayload();
  const cv = await apiPatch(`/cvs/${CV_STATE.activeCvId}`, payload);
  CV_STATE.activeCv = cv;
  CV_STATE.repository = CV_STATE.repository.map((item) =>
    item.cv_id === cv.cv_id ? cv : item
  );
  renderCVRepository();
  renderActiveCVMeta(cv);
  return cv;
}

async function duplicateActiveCV() {
  if (!CV_STATE.activeCvId) {
    showToast("Open a CV before duplicating it", "info");
    return;
  }

  try {
    const copy = await apiPost(`/cvs/${CV_STATE.activeCvId}/duplicate`, {
      name: `${CV_STATE.activeCv?.name || "CV"} Copy`,
    });
    CV_STATE.repository = [copy, ...CV_STATE.repository];
    renderCVDocument(copy);
    renderCVRepository();
    showToast("CV duplicated", "success");
  } catch (err) {
    showToast("Could not duplicate CV: " + err.message, "error");
  }
}

function initCVAgentWorkspace() {
  const sourceSelect = document.getElementById("cv-source-select");
  const sourceText = document.getElementById("cv-source-text");
  if (!sourceSelect || !sourceText) return;

  sourceSelect.addEventListener("change", () => {
    sourceText.classList.toggle("is-hidden", sourceSelect.value !== "paste");
  });
}

function clearCVAgentWorkspace() {
  document.getElementById("cv-role-input").value = "";
  document.getElementById("cv-source-text").value = "";
  document.getElementById("cv-agent-output").innerHTML =
    "<span class='text-muted text-sm'>Agent drafts, change summaries, and role-fit notes will appear here.</span>";
  CV_STATE.agentDraft = null;
}

function renderAgentList(title, items) {
  if (!items?.length) return "";
  return `<h3>${escapeHTML(title)}</h3><ul>${items.map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>`;
}

function cvDocumentFromAgentDraft(draft, name) {
  const roleDescription = document.getElementById("cv-role-input")?.value.trim() || "";
  const fallbackName = roleDescription
    ? `${roleDescription.split(/\r?\n/)[0].slice(0, 64)} CV`
    : "Tailored CV";

  return {
    professional_id: CURRENT_USER_ID,
    name: name || fallbackName,
    target_role: roleDescription || null,
    source_type: "agent",
    tags: ["tailored"],
    cv_contact: draft.tailored_cv_contact || collectCVContact(),
    cv_overview: draft.tailored_cv_overview || "",
    skills: draft.tailored_skills || [],
    cv_sections: draft.tailored_cv_sections || {},
    is_default: false,
  };
}

function applyAgentDraftToCurrentCV() {
  const draft = CV_STATE.agentDraft;
  if (!draft) {
    showToast("Run the CV agent before applying a draft", "info");
    return;
  }

  const previewCv = {
    cv_id: CV_STATE.activeCvId || "agent-preview",
    name: CV_STATE.activeCv?.name || "Agent Preview",
    target_role: document.getElementById("cv-role-input")?.value.trim() || null,
    cv_contact: draft.tailored_cv_contact || {},
    cv_overview: draft.tailored_cv_overview || "",
    skills: draft.tailored_skills || [],
    cv_sections: draft.tailored_cv_sections || {},
  };

  renderCVDocument(previewCv);
  renderResumePreview(previewCv);
  showToast("Agent draft applied to the editor. Save CV to persist it.", "success");
}

async function saveAgentDraftAsNewCV() {
  const draft = CV_STATE.agentDraft;
  if (!draft) {
    showToast("Run the CV agent before saving a tailored CV", "info");
    return;
  }

  try {
    const created = await apiPost("/cvs", cvDocumentFromAgentDraft(draft));
    CV_STATE.repository = [created, ...CV_STATE.repository];
    renderCVDocument(created);
    renderCVRepository();
    showToast("Tailored CV saved to repository", "success");
  } catch (err) {
    showToast("Could not save tailored CV: " + err.message, "error");
  }
}

async function runCVAgentPreview() {
  const roleInput = document.getElementById("cv-role-input");
  const sourceSelect = document.getElementById("cv-source-select");
  const sourceText = document.getElementById("cv-source-text");
  const output = document.getElementById("cv-agent-output");
  const roleDescription = roleInput.value.trim();

  if (!roleDescription) {
    showToast("Paste a target role before tailoring", "info");
    return;
  }

  CV_STATE.isTailoring = true;
  output.innerHTML = "<span class='spinner'></span> Tailoring CV...";

  try {
    const result = await apiPost("/agents/cv-tailor", {
      professional_id: CURRENT_USER_ID,
      cv_id: sourceSelect.value === "active" ? CV_STATE.activeCvId : null,
      role_description: roleDescription,
      source_cv_text: sourceSelect.value === "paste" ? sourceText.value.trim() : null,
      output_mode: "preview",
    });

    CV_STATE.agentDraft = result;
    output.innerHTML = `
      ${renderAgentList("Changes", result.changes_summary)}
      ${renderAgentList("Role alignment", result.role_alignment)}
      ${renderAgentList("Gaps to review", result.missing_experience)}
      ${renderAgentList("Suggested keywords", result.suggested_keywords)}
      ${renderAgentList("Warnings", result.warnings)}
      <div class="cv-agent-actions">
        <button class="btn btn-primary btn-sm" type="button" onclick="applyAgentDraftToCurrentCV()">Apply to current CV</button>
        <button class="btn btn-secondary btn-sm" type="button" onclick="saveAgentDraftAsNewCV()">Save as new CV</button>
      </div>
      <div class="cv-agent-preview">${escapeHTML(result.tailored_cv_text)}</div>
    `;
    showToast("Tailored CV draft ready", "success");
  } catch (err) {
    output.innerHTML = `<span style="color:var(--ibm-red)">CV tailor failed: ${err.message}</span>`;
  } finally {
    CV_STATE.isTailoring = false;
  }
}

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
    const cvEditor = document.getElementById("cv-editor");
    if (cvEditor) {
      cvEditor.value = profile.cv_overview || "";
    }

    const skillsEditor = document.getElementById("cv-skills-editor");
    if (skillsEditor) {
      skillsEditor.value = profile.skills?.join("\n") || "";
    }
    renderCVContact(profile);
    renderCVSections(profile);
    renderResumePreview({
      name: profile.name,
      target_role: null,
      cv_contact: profile.cv_contact || {},
      cv_overview: profile.cv_overview || "",
      skills: profile.skills || [],
      cv_sections: profile.cv_sections || {},
    });
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
          <div class="ai-panel-header"><span class="ai-icon"></span> Draft nudge to owner</div>
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
  if (!CURRENT_USER_ID) {
    container.innerHTML = "<p class='text-muted text-sm'>Sign in to see personalized seat recommendations.</p>";
    return;
  }
  container.innerHTML = '<span class="spinner"></span>';
  try {
    const result = await apiPost("/agents/recommendations", {
      professional_id: CURRENT_USER_ID,
      mode: "candidate",
      limit: 5,
    });
    if (!result.recommendations.length) {
      container.innerHTML = `<p class='text-muted'>${result.reasoning || "No recommendations available."}</p>`;
      return;
    }
    const warningHtml = (result.warnings || [])
      .map((w) => `<p class="text-sm text-muted" style="margin-bottom:.35rem">${w}</p>`)
      .join("");
    container.innerHTML = `
      <p class="text-sm text-muted" style="margin-bottom:.75rem">${result.reasoning || ""}</p>
      ${warningHtml}
      <ul class="rec-list">
        ${result.recommendations
          .map(
            (r) => `
          <li class="rec-item" style="cursor:pointer" onclick="window.location.href='seat-detail.html?id=${encodeURIComponent(r.seat_id)}&backend_port=${localStorage.getItem('BACKEND_PORT') || '8000'}'">
            <div>
              <div style="font-weight:600;font-size:13px">${r.title || r.seat_id}</div>
              <div class="text-sm text-muted">${r.client_name || ""}</div>
              <div class="rec-reason">${r.reason}</div>
              ${
                r.aligned_skills && r.aligned_skills.length
                  ? `<div class="text-sm" style="margin-top:.25rem;color:var(--ibm-blue)">${r.aligned_skills.slice(0, 4).join(" · ")}</div>`
                  : ""
              }
            </div>
            <div class="rec-score">${Math.round((r.match_score || 0) * 100)}% match</div>
          </li>`
          )
          .join("")}
      </ul>
      <div style="margin-top:.75rem">
        <button class="btn btn-secondary btn-sm" type="button" onclick="loadRecommendations()">Refresh recommendations</button>
      </div>`;
  } catch (err) {
    container.innerHTML = `<p class="text-muted text-sm">Could not load recommendations${err?.message ? `: ${err.message}` : "."}</p>
      <button class="btn btn-secondary btn-sm" type="button" onclick="loadRecommendations()">Retry</button>`;
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
  window.location.href = `seat-detail.html?id=${seatId}&backend_port=${localStorage.getItem('BACKEND_PORT') || '8000'}`;
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
          <button class="btn btn-ghost btn-sm" onclick="runMismatchCheck('${seat.seat_id}')">Check mismatch</button>
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

async function saveCVEdits() {
  const editor = document.getElementById("cv-editor");
  if (!editor || !CURRENT_USER_ID) return;

  const cvPayload = collectCurrentCVPayload();

  try {
    const profile = await apiPatch(`/profile/${CURRENT_USER_ID}`, {
      cv_overview: cvPayload.cv_overview,
      cv_contact: cvPayload.cv_contact,
      cv_sections: cvPayload.cv_sections,
      skills: cvPayload.skills,
    });

    const activeCv = await saveActiveCVDocument();
    document.getElementById("prof-skills").textContent =
      profile.skills?.join(", ") || "â€”";
    renderCVContact(profile);
    renderCVSections(profile);
    if (activeCv) {
      renderCVDocument(activeCv);
    } else {
      renderResumePreview({
        name: profile.name,
        target_role: null,
        cv_contact: profile.cv_contact || {},
        cv_overview: profile.cv_overview || "",
        skills: profile.skills || [],
        cv_sections: profile.cv_sections || {},
      });
    }
    updateCVTimestamp();
    showToast("CV changes saved in ProM", "success");
  } catch (err) {
    showToast("Could not save CV changes: " + err.message, "error");
  }
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
  // owner.html also loads prom.js for shared helpers (toast/logout). Skip candidate SPA init there.
  if (!document.getElementById("page-profile")) {
    return;
  }

  // Check authentication first
  if (!checkAuth()) {
    return;
  }

  updateUserDisplay();

  initTabs();
  initCollapse();
  initCVBuilderNav();
  initCVActionButtons();
  initCVAgentWorkspace();
  initSeatCards();

  // Load profile data
  loadProfile();
  loadCVRepository();
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
