/**
 * GitHub-style activity heatmap — periods, labels, tooltips, display options.
 */

const Heatmap = {
  PERIODS: {
    "4w": { weeks: 4, label: "Last 4 weeks" },
    "3m": { weeks: 13, label: "Last 3 months" },
    "6m": { weeks: 26, label: "Last 6 months" },
    "1y": { weeks: 52, label: "Last year" },
  },

  prefs: {
    period: localStorage.getItem("df-heatmap-period") || "1y",
    showFreezes: localStorage.getItem("df-heatmap-freezes") !== "false",
    weekStart: localStorage.getItem("df-heatmap-weekstart") || "sunday",
  },

  _cells: [],
  _tooltip: null,

  init() {
    this._tooltip = document.getElementById("heatmap-tooltip");
    this._bindControls();
  },

  _bindControls() {
    const periodSelect = document.getElementById("heatmap-period");
    const freezeToggle = document.getElementById("heatmap-show-freezes");
    const weekStartSelect = document.getElementById("heatmap-week-start");

    if (periodSelect) {
      periodSelect.innerHTML = Object.entries(this.PERIODS)
        .map(([k, v]) => `<option value="${k}">${v.label}</option>`)
        .join("");
      periodSelect.value = this.prefs.period;
      periodSelect.addEventListener("change", () => {
        this.prefs.period = periodSelect.value;
        localStorage.setItem("df-heatmap-period", this.prefs.period);
        this.reload();
      });
    }

    if (freezeToggle) {
      freezeToggle.checked = this.prefs.showFreezes;
      freezeToggle.addEventListener("change", () => {
        this.prefs.showFreezes = freezeToggle.checked;
        localStorage.setItem("df-heatmap-freezes", String(this.prefs.showFreezes));
        this.render(this._cells);
      });
    }

    if (weekStartSelect) {
      weekStartSelect.value = this.prefs.weekStart;
      weekStartSelect.addEventListener("change", () => {
        this.prefs.weekStart = weekStartSelect.value;
        localStorage.setItem("df-heatmap-weekstart", this.prefs.weekStart);
        this.render(this._cells);
      });
    }
  },

  getWeeks() {
    return this.PERIODS[this.prefs.period]?.weeks || 52;
  },

  async reload() {
    const weeks = this.getWeeks();
    const res = await fetch(`/api/stats?${Settings.tzParam()}&weeks=${weeks}`);
    if (!res.ok) return;
    const stats = await res.json();
    this.render(stats.heatmap);
    return stats;
  },

  render(cells) {
    this._cells = cells || [];
    const grid = document.getElementById("heatmap-grid");
    const monthsEl = document.getElementById("heatmap-months");
    const daysEl = document.getElementById("heatmap-day-labels");
    if (!grid) return;

    const weekStart = this.prefs.weekStart === "monday" ? 1 : 0;
    const weeks = this._groupIntoWeeks(this._cells, weekStart);

    // --- Month labels (GitHub-style, spanning week columns) ---
    if (monthsEl) {
      monthsEl.innerHTML = "";
      monthsEl.style.gridTemplateColumns = `repeat(${weeks.length}, 12px)`;

      const spans = [];
      let cur = null;
      weeks.forEach((week, wi) => {
        const first = week.find((c) => c);
        if (!first) return;
        const m = new Date(first.date + "T12:00:00").getMonth();
        if (!cur || cur.month !== m) {
          if (cur) spans.push(cur);
          cur = {
            month: m,
            start: wi + 1,
            count: 1,
            label: new Date(first.date + "T12:00:00").toLocaleDateString(undefined, { month: "short" }),
          };
        } else {
          cur.count += 1;
        }
      });
      if (cur) spans.push(cur);

      spans.forEach((s) => {
        const el = document.createElement("span");
        el.className = "heatmap-month-label";
        el.textContent = s.label;
        el.style.gridColumn = `${s.start} / span ${s.count}`;
        monthsEl.appendChild(el);
      });
    }

    // --- Day labels (Mon / Wed / Fri like GitHub) ---
    if (daysEl) {
      const labels = weekStart === 1
        ? ["", "Mon", "", "Wed", "", "Fri", ""]
        : ["", "Mon", "", "Wed", "", "Fri", ""];
      daysEl.innerHTML = labels
        .map((l) => `<span class="heatmap-day-label">${l}</span>`)
        .join("");
    }

    // --- Grid: 7 rows × N week columns ---
    grid.innerHTML = "";
    grid.style.gridTemplateColumns = `repeat(${weeks.length}, 1fr)`;
    grid.style.gridTemplateRows = "repeat(7, 1fr)";

    const maxRow = 7;
    weeks.forEach((week, col) => {
      week.forEach((cell, row) => {
        const el = document.createElement("div");
        el.className = "heatmap-cell";
        el.style.gridColumn = col + 1;
        el.style.gridRow = row + 1;

        if (cell) {
          const level = this._displayLevel(cell);
          el.dataset.level = level;
          el.dataset.date = cell.date;
          el.addEventListener("mouseenter", (e) => this._showTooltip(e, cell));
          el.addEventListener("mouseleave", () => this._hideTooltip());
        } else {
          el.classList.add("heatmap-cell--empty");
        }
        grid.appendChild(el);
      });
    });

    const scroll = document.querySelector(".heatmap-scroll");
    if (scroll) scroll.scrollLeft = scroll.scrollWidth;

    const rangeEl = document.getElementById("heatmap-range");
    if (rangeEl && this._cells.length > 0) {
      const fmt = (iso) => {
        const d = new Date(iso + "T12:00:00");
        return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
      };
      rangeEl.textContent = `${fmt(this._cells[0].date)} – ${fmt(this._cells[this._cells.length - 1].date)}`;
    }
  },

  _displayLevel(cell) {
    if (cell.posted) return cell.level ?? 0;
    if (cell.frozen && this.prefs.showFreezes) return 1;
    return 0;
  },

  _groupIntoWeeks(cells, weekStart) {
    if (!cells.length) return [];

    const weeks = [];
    let column = new Array(7).fill(null);

    cells.forEach((cell, idx) => {
      const d = new Date(cell.date + "T12:00:00");
      let row = d.getDay();
      if (weekStart === 1) row = (row + 6) % 7;

      if (idx > 0) {
        const newWeek = weekStart === 0 ? d.getDay() === 0 : d.getDay() === 1;
        if (newWeek) {
          weeks.push(column);
          column = new Array(7).fill(null);
        }
      }

      column[row] = cell;
      if (idx === cells.length - 1) weeks.push(column);
    });

    return weeks;
  },

  _showTooltip(event, cell) {
    if (!this._tooltip) return;
    const d = new Date(cell.date + "T12:00:00");
    const dateStr = d.toLocaleDateString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });

    let activity;
    if (cell.posted) {
      const kind = cell.post_type === "thread" ? "thread" : "post";
      activity = `<strong>1 ${kind}</strong>`;
    } else if (cell.frozen) {
      activity = "<strong>Streak freeze</strong>";
    } else {
      activity = "<strong>No posts</strong>";
    }

    this._tooltip.innerHTML = `${activity} on ${dateStr}`;
    this._tooltip.hidden = false;

    const rect = event.target.getBoundingClientRect();
    this._tooltip.style.left = `${rect.left + rect.width / 2}px`;
    this._tooltip.style.top = `${rect.top - 8}px`;
  },

  _hideTooltip() {
    if (this._tooltip) this._tooltip.hidden = true;
  },
};