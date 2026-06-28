/**
 * Daily Forge — client-side application logic.
 */

const API = {
  prompt: () => fetch("/api/prompt").then((r) => r.json()),
  stats: () => fetch("/api/stats").then((r) => r.json()),
  today: () => fetch("/api/today").then((r) => (r.ok && r.status !== 204 ? r.json() : null)),
  post: (body) =>
    fetch("/api/post", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => r.json()),
  formatThread: (items) =>
    fetch("/api/thread/format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    }).then((r) => r.json()),
};

// --- Theme ---

function initTheme() {
  const saved = localStorage.getItem("df-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (prefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);
  updateThemeIcon(theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("df-theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
}

// --- Toast ---

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

// --- Clipboard ---

async function copyText(text, label = "Copied!") {
  try {
    await navigator.clipboard.writeText(text);
    showToast(label);
    return true;
  } catch {
    showToast("Copy failed — select text manually");
    return false;
  }
}

// --- Character count ---

const X_LIMIT = 280;
const LINKEDIN_LIMIT = 3000;

function updateCharCount(textarea, counterEl, limit) {
  const len = textarea.value.length;
  counterEl.textContent = `${len} / ${limit}`;
  counterEl.classList.remove("warning", "danger");
  if (len > limit) counterEl.classList.add("danger");
  else if (len > limit * 0.9) counterEl.classList.add("warning");
}

// --- Heatmap ---

function renderHeatmap(cells) {
  const container = document.getElementById("heatmap-grid");
  container.innerHTML = "";

  // Group cells into weeks (columns).
  const weeks = [];
  let currentWeek = [];

  cells.forEach((cell, i) => {
    const d = new Date(cell.date + "T12:00:00");
    const dayOfWeek = d.getDay();

    if (i === 0 && dayOfWeek !== 0) {
      for (let pad = 0; pad < dayOfWeek; pad++) {
        currentWeek.push(null);
      }
    }

    currentWeek.push(cell);
    if (dayOfWeek === 6 || i === cells.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  weeks.forEach((week) => {
    const weekEl = document.createElement("div");
    weekEl.className = "heatmap-week";
    week.forEach((cell) => {
      const el = document.createElement("div");
      if (cell) {
        el.className = "heatmap-cell";
        el.dataset.level = cell.level;
        el.title = `${cell.date}: ${cell.count ? "Posted" : "No post"}`;
      } else {
        el.className = "heatmap-cell";
        el.style.visibility = "hidden";
      }
      weekEl.appendChild(el);
    });
    container.appendChild(weekEl);
  });
}

// --- Stats ---

async function loadStats() {
  const stats = await API.stats();

  document.getElementById("current-streak").textContent = stats.current_streak;
  document.getElementById("longest-streak").textContent = stats.longest_streak;
  document.getElementById("total-posts").textContent = stats.total_posts;

  const banner = document.getElementById("status-banner");
  banner.textContent = stats.message;
  banner.className = `status-banner ${stats.status}`;

  renderHeatmap(stats.heatmap);

  const markBtn = document.getElementById("mark-posted-btn");
  if (stats.posted_today) {
    markBtn.textContent = "✓ Posted today";
    markBtn.classList.remove("btn-primary");
    markBtn.classList.add("btn-success");
  } else {
    markBtn.textContent = "Mark as posted";
    markBtn.classList.remove("btn-success");
    markBtn.classList.add("btn-primary");
  }
}

// --- Prompt ---

async function loadPrompt() {
  const { prompt } = await API.prompt();
  document.getElementById("prompt-text").textContent = prompt;
}

// --- Mode tabs ---

function initModeTabs() {
  const tabs = document.querySelectorAll(".mode-tab");
  const panels = document.querySelectorAll(".composer-panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(tab.dataset.panel).classList.add("active");
    });
  });
}

// --- Single post mode ---

function initSinglePost() {
  const textarea = document.getElementById("single-content");
  const counter = document.getElementById("single-char-count");

  textarea.addEventListener("input", () => updateCharCount(textarea, counter, X_LIMIT));

  document.getElementById("copy-x-btn").addEventListener("click", () => {
    copyText(textarea.value, "Copied for X!");
  });

  document.getElementById("copy-linkedin-btn").addEventListener("click", () => {
    copyText(textarea.value, "Copied for LinkedIn!");
  });
}

// --- Thread mode ---

function initThreadMode() {
  const container = document.getElementById("thread-items");
  const addBtn = document.getElementById("add-thread-item");
  const formatBtn = document.getElementById("format-thread-btn");
  const preview = document.getElementById("thread-preview");
  const copyThreadBtn = document.getElementById("copy-thread-btn");

  let formattedThread = "";

  function addThreadItem(value = "") {
    const index = container.children.length + 1;
    const row = document.createElement("div");
    row.className = "thread-item-row";
    row.innerHTML = `
      <span class="thread-number">${index}</span>
      <textarea class="thread-input" rows="2" placeholder="Point ${index}...">${value}</textarea>
    `;
    container.appendChild(row);
    renumberItems();
  }

  function renumberItems() {
    container.querySelectorAll(".thread-item-row").forEach((row, i) => {
      row.querySelector(".thread-number").textContent = i + 1;
      row.querySelector(".thread-input").placeholder = `Point ${i + 1}...`;
    });
  }

  function getThreadItems() {
    return [...container.querySelectorAll(".thread-input")].map((el) => el.value);
  }

  addBtn.addEventListener("click", () => addThreadItem());

  formatBtn.addEventListener("click", async () => {
    const items = getThreadItems();
    if (!items.some((i) => i.trim())) {
      showToast("Add at least one point");
      return;
    }
    const result = await API.formatThread(items);
    formattedThread = result.formatted;
    preview.textContent = formattedThread;
    preview.classList.add("visible");
    showToast(`Thread formatted (${result.tweet_count} posts)`);
  });

  copyThreadBtn.addEventListener("click", () => {
    if (!formattedThread) {
      showToast("Format the thread first");
      return;
    }
    copyText(formattedThread, "Thread copied!");
  });

  // Start with 3 empty items.
  for (let i = 0; i < 3; i++) addThreadItem();
}

// --- Mark posted ---

function initMarkPosted() {
  document.getElementById("mark-posted-btn").addEventListener("click", async () => {
    const activePanel = document.querySelector(".composer-panel.active");
    let content = null;
    let post_type = "single";

    if (activePanel.id === "panel-single") {
      content = document.getElementById("single-content").value || null;
      post_type = "single";
    } else {
      const preview = document.getElementById("thread-preview");
      content = preview.classList.contains("visible") ? preview.textContent : null;
      post_type = "thread";
    }

    await API.post({ content, post_type });
    showToast("Streak updated — you showed up!");
    await loadStats();
  });
}

// --- Load today's entry ---

async function loadTodayEntry() {
  try {
    const entry = await API.today();
    if (!entry) return;

    if (entry.post_type === "thread" && entry.content) {
      document.querySelector('[data-panel="panel-thread"]').click();
      document.getElementById("thread-preview").textContent = entry.content;
      document.getElementById("thread-preview").classList.add("visible");
    } else if (entry.content) {
      document.getElementById("single-content").value = entry.content;
      updateCharCount(
        document.getElementById("single-content"),
        document.getElementById("single-char-count"),
        X_LIMIT
      );
    }
  } catch {
    // No entry today — that's fine.
  }
}

// --- Init ---

document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  initModeTabs();
  initSinglePost();
  initThreadMode();
  initMarkPosted();

  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  await Promise.all([loadPrompt(), loadStats(), loadTodayEntry()]);
});