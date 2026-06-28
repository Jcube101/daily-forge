/**
 * Daily Forge v0.2 — main application orchestration.
 */

const API = {
  prompt: () => fetch(`/api/prompt?${Settings.tzParam()}`).then((r) => r.json()),
  stats: () => {
    const weeks = typeof Heatmap !== "undefined" ? Heatmap.getWeeks() : 52;
    return fetch(`/api/stats?${Settings.tzParam()}&weeks=${weeks}`).then((r) => r.json());
  },
  today: () =>
    fetch(`/api/today?${Settings.tzParam()}`).then((r) =>
      r.ok && r.status !== 204 ? r.json() : null
    ),
  post: (body) =>
    fetch("/api/post", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...body, timezone: Settings.timezone }),
    }).then((r) => r.json()),
  formatThread: (items) =>
    fetch("/api/thread/format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    }).then((r) => r.json()),
  splitThread: (items) =>
    fetch("/api/thread/split", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items, max_len: 280 }),
    }).then((r) => r.json()),
  freeze: (freezeDate) =>
    fetch("/api/freeze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ freeze_date: freezeDate, timezone: Settings.timezone }),
    }).then((r) => {
      if (!r.ok) return r.json().then((e) => Promise.reject(e));
      return r.json();
    }),
};

let currentPlatform = "x";
let formattedThread = "";
let draftSaveTimer = null;

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
  if (!text?.trim()) {
    showToast("Nothing to copy");
    return false;
  }
  try {
    await navigator.clipboard.writeText(text);
    showToast(label);
    return true;
  } catch {
    showToast("Copy failed — select text manually");
    return false;
  }
}

// --- Stats ---

async function loadStats() {
  const weeks = Heatmap.getWeeks();
  const stats = await fetch(`/api/stats?${Settings.tzParam()}&weeks=${weeks}`).then((r) => r.json());

  document.getElementById("current-streak").textContent = stats.current_streak;
  document.getElementById("longest-streak").textContent = stats.longest_streak;
  document.getElementById("total-posts").textContent = stats.total_posts;

  const banner = document.getElementById("status-banner");
  banner.textContent = stats.message;
  banner.className = `status-banner ${stats.status}`;

  Heatmap.render(stats.heatmap);
  updateEmptyState(stats.total_posts);

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

  const freezeInfo = document.getElementById("freeze-info");
  if (freezeInfo) {
    freezeInfo.textContent = `${stats.freezes_remaining} streak freeze${stats.freezes_remaining === 1 ? "" : "s"} left this month`;
  }

  return stats;
}

function updateEmptyState(totalPosts) {
  const el = document.getElementById("empty-state");
  if (el) el.classList.toggle("hidden", totalPosts > 0);
}

// --- Prompt ---

async function loadPrompt() {
  const { prompt } = await API.prompt();
  document.getElementById("prompt-text").textContent = prompt;
}

// --- Mode tabs ---

function initModeTabs() {
  document.querySelectorAll(".mode-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".mode-tab").forEach((t) => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".composer-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      document.getElementById(tab.dataset.panel).classList.add("active");
    });
  });
}

// --- Platform toggle ---

function initPlatformToggle() {
  currentPlatform = Drafts.loadPlatform();
  document.querySelectorAll(".platform-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.platform === currentPlatform);
    btn.addEventListener("click", () => {
      currentPlatform = btn.dataset.platform;
      Drafts.savePlatform(currentPlatform);
      document.querySelectorAll(".platform-btn").forEach((b) =>
        b.classList.toggle("active", b.dataset.platform === currentPlatform)
      );
      updatePlatformGuidance();
      const textarea = document.getElementById("single-content");
      CharCount.update(textarea, document.getElementById("single-char-count"), currentPlatform);
    });
  });
  updatePlatformGuidance();
}

function updatePlatformGuidance() {
  const box = document.getElementById("platform-tips");
  if (!box) return;
  const tips = CharCount.tips[currentPlatform] || [];
  box.innerHTML = tips.map((t) => `<li>${t}</li>`).join("");
}

// --- Single post ---

function initSinglePost() {
  const textarea = document.getElementById("single-content");
  const counter = document.getElementById("single-char-count");

  const draft = Drafts.loadSingle();
  if (draft) textarea.value = draft;

  const onInput = () => {
    CharCount.update(textarea, counter, currentPlatform);
    clearTimeout(draftSaveTimer);
    draftSaveTimer = setTimeout(() => Drafts.saveSingle(textarea.value), 400);
  };
  textarea.addEventListener("input", onInput);
  onInput();

  document.getElementById("copy-x-btn").addEventListener("click", () =>
    copyText(textarea.value, "Copied for X!")
  );
  document.getElementById("copy-linkedin-btn").addEventListener("click", () =>
    copyText(textarea.value, "Copied for LinkedIn!")
  );
}

// --- Thread mode ---

function initThreadMode() {
  const container = document.getElementById("thread-items");
  const preview = document.getElementById("thread-preview");
  const splitPreview = document.getElementById("thread-split-preview");

  function addThreadItem(value = "") {
    const row = document.createElement("div");
    row.className = "thread-item-row";
    const index = container.children.length + 1;
    row.innerHTML = `
      <span class="thread-number">${index}</span>
      <textarea class="thread-input" rows="2" placeholder="Point ${index}...">${value}</textarea>
    `;
    container.appendChild(row);
    renumberItems();
    row.querySelector(".thread-input").addEventListener("input", saveThreadDraft);
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

  function saveThreadDraft() {
    clearTimeout(draftSaveTimer);
    draftSaveTimer = setTimeout(() => {
      Drafts.saveThread(preview.textContent, getThreadItems());
    }, 400);
  }

  document.getElementById("add-thread-item").addEventListener("click", () => addThreadItem());

  document.getElementById("format-thread-btn").addEventListener("click", async () => {
    const items = getThreadItems();
    if (!items.some((i) => i.trim())) {
      showToast("Add at least one point");
      return;
    }
    const result = await API.formatThread(items);
    formattedThread = result.formatted;
    preview.textContent = formattedThread;
    preview.classList.add("visible");
    Drafts.saveThread(formattedThread, items);
    showToast(`Thread formatted (${result.tweet_count} posts)`);
    await renderSplitPreview(items);
  });

  document.getElementById("copy-thread-btn").addEventListener("click", () => {
    if (!formattedThread) {
      showToast("Format the thread first");
      return;
    }
    copyText(formattedThread, "Thread copied!");
  });

  async function renderSplitPreview(items) {
    const res = await API.splitThread(items);
    if (!splitPreview) return;
    splitPreview.innerHTML = res.chunks
      .map(
        (c) => `
      <div class="split-chunk">
        <div class="split-chunk-header">Tweet ${c.index}/${c.total} · ${c.weighted_chars}/280</div>
        <div class="split-chunk-body">${escapeHtml(c.text)}</div>
      </div>`
      )
      .join("");
    splitPreview.classList.add("visible");
  }

  // Restore draft or start with 3 items.
  const threadDraft = Drafts.loadThread();
  if (threadDraft.items.length) {
    threadDraft.items.forEach((item) => addThreadItem(item));
    if (threadDraft.formatted) {
      formattedThread = threadDraft.formatted;
      preview.textContent = formattedThread;
      preview.classList.add("visible");
    }
  } else {
    for (let i = 0; i < 3; i++) addThreadItem();
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// --- Mark posted ---

async function markPosted() {
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
  Drafts.clearSingle();
  await loadStats();
  await Recap.load().then(Recap.render);
}

function initMarkPosted() {
  document.getElementById("mark-posted-btn").addEventListener("click", markPosted);
}

// --- Streak freeze ---

function initFreeze() {
  document.getElementById("use-freeze-btn")?.addEventListener("click", async () => {
    const input = document.getElementById("freeze-date");
    const freezeDate = input?.value;
    if (!freezeDate) {
      showToast("Pick a date to freeze");
      return;
    }
    try {
      await API.freeze(freezeDate);
      showToast("Streak freeze applied!");
      input.value = "";
      await loadStats();
      await Recap.load().then(Recap.render);
    } catch (err) {
      showToast(err.detail || "Could not apply freeze");
    }
  });
}

// --- Settings panel ---

function initSettings() {
  const tzSelect = document.getElementById("timezone-select");
  if (tzSelect) {
    Intl.supportedValuesOf("timeZone").forEach((z) => {
      const opt = document.createElement("option");
      opt.value = z;
      opt.textContent = z.replace(/_/g, " ");
      if (z === Settings.timezone) opt.selected = true;
      tzSelect.appendChild(opt);
    });
    tzSelect.addEventListener("change", async () => {
      Settings.timezone = tzSelect.value;
      await Settings.syncToServer();
      await refreshAll();
      showToast("Timezone updated");
    });
  }

  const reminderToggle = document.getElementById("reminder-toggle");
  const reminderTime = document.getElementById("reminder-time");
  if (reminderToggle) {
    reminderToggle.checked = Settings.reminderEnabled;
    reminderToggle.addEventListener("change", async () => {
      Settings.reminderEnabled = reminderToggle.checked;
      if (Settings.reminderEnabled) {
        const perm = await Notifications.requestPermission();
        if (perm !== "granted") {
          Settings.reminderEnabled = false;
          reminderToggle.checked = false;
          showToast("Notification permission denied");
          return;
        }
      }
      await Settings.syncToServer();
      Notifications.startReminderCheck();
      showToast(Settings.reminderEnabled ? "Reminders enabled" : "Reminders off");
    });
  }
  if (reminderTime) {
    reminderTime.value = Settings.reminderTime;
    reminderTime.addEventListener("change", async () => {
      Settings.reminderTime = reminderTime.value;
      await Settings.syncToServer();
    });
  }

  document.getElementById("settings-toggle")?.addEventListener("click", () => {
    document.getElementById("settings-panel")?.classList.toggle("open");
  });

  document.getElementById("export-md-btn")?.addEventListener("click", () => {
    window.location.href = "/api/export/markdown";
    showToast("Downloading history…");
  });
}

// --- Keyboard shortcuts ---

function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === "Enter") {
      e.preventDefault();
      markPosted();
    }
    if (mod && e.key === "s") {
      e.preventDefault();
      const textarea = document.getElementById("single-content");
      Drafts.saveSingle(textarea.value);
      Drafts.saveThread(
        document.getElementById("thread-preview")?.textContent,
        [...document.querySelectorAll(".thread-input")].map((el) => el.value)
      );
      showToast("Draft saved");
    }
  });
}

// --- Load today's entry ---

async function loadTodayEntry() {
  try {
    const entry = await API.today();
    if (!entry) return;
    if (entry.post_type === "thread" && entry.content) {
      document.querySelector('[data-panel="panel-thread"]')?.click();
      const preview = document.getElementById("thread-preview");
      preview.textContent = entry.content;
      preview.classList.add("visible");
      formattedThread = entry.content;
    } else if (entry.content && !Drafts.loadSingle()) {
      document.getElementById("single-content").value = entry.content;
      CharCount.update(
        document.getElementById("single-content"),
        document.getElementById("single-char-count"),
        currentPlatform
      );
    }
  } catch {
    // No entry today.
  }
}

async function refreshAll() {
  await Promise.all([
    loadPrompt(),
    loadStats(),
    loadTodayEntry(),
    Recap.load().then(Recap.render),
  ]);
}

// --- Init ---

document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  await Settings.loadFromServer();
  await Notifications.registerServiceWorker();
  Heatmap.init();

  initModeTabs();
  initPlatformToggle();
  initSinglePost();
  initThreadMode();
  initMarkPosted();
  initFreeze();
  initSettings();
  initKeyboardShortcuts();

  document.getElementById("theme-toggle")?.addEventListener("click", toggleTheme);

  await refreshAll();
  Onboarding.show();
  Notifications.startReminderCheck();
});