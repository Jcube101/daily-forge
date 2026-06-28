/**
 * Weekly recap view rendering.
 */

const Recap = {
  async load() {
    const res = await fetch(`/api/weekly-recap?${Settings.tzParam()}`);
    if (!res.ok) return null;
    return res.json();
  },

  render(data) {
    const section = document.getElementById("weekly-recap");
    if (!section || !data) return;

    const trendBars = data.streak_trend
      .map(
        (d) => `
        <div class="trend-bar-wrap" title="${d.date}">
          <div class="trend-bar ${d.covered ? "covered" : ""}"></div>
          <span class="trend-label">${d.day_label}</span>
        </div>`
      )
      .join("");

    const weekList = data.week_days
      .filter((d) => d.posted || d.frozen)
      .map((d) => {
        const icon = d.frozen && !d.posted ? "🧊" : "✓";
        const preview = d.content_preview ? `<span class="recap-preview">${d.content_preview}…</span>` : "";
        return `<li class="recap-item">${icon} <strong>${d.day_label}</strong> ${preview}</li>`;
      })
      .join("");

    section.innerHTML = `
      <h2 class="section-title">This week</h2>
      <div class="recap-stats">
        <div class="recap-stat"><span class="recap-stat-val">${data.posts_this_week}</span> posts</div>
        <div class="recap-stat"><span class="recap-stat-val">${data.days_covered}/7</span> days covered</div>
        <div class="recap-stat"><span class="recap-stat-val">${data.current_streak}</span> day streak</div>
      </div>
      <div class="trend-chart" aria-label="7-day streak trend">${trendBars}</div>
      <ul class="recap-list">${weekList || '<li class="recap-empty">No posts yet this week — today is a great start.</li>'}</ul>
    `;
  },
};