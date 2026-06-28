/**
 * Character counting — X URL-weighted + platform guidance.
 */

const URL_PATTERN = /https?:\/\/\S+/g;
const X_URL_WEIGHT = 23;
const X_LIMIT = 280;
const LINKEDIN_LIMIT = 3000;

const CharCount = {
  countX(text) {
    if (!text) return 0;
    const urls = text.match(URL_PATTERN) || [];
    const urlChars = urls.reduce((sum, u) => sum + u.length, 0);
    return text.length - urlChars + urls.length * X_URL_WEIGHT;
  },

  update(textarea, counterEl, platform = "x") {
    const raw = textarea.value.length;
    const weighted = this.countX(textarea.value);
    const limit = platform === "x" ? X_LIMIT : LINKEDIN_LIMIT;
    const display = platform === "x" ? weighted : raw;

    let hint = "";
    if (platform === "x" && weighted !== raw) {
      hint = ` (${raw} raw, URLs weighted)`;
    }

    counterEl.textContent = `${display} / ${limit}${hint}`;
    counterEl.classList.remove("warning", "danger");
    if (display > limit) counterEl.classList.add("danger");
    else if (display > limit * 0.9) counterEl.classList.add("warning");

    return { raw, weighted, display, limit, over: display > limit };
  },

  tips: {
    x: [
      "Keep posts under 280 characters (URLs count as 23 each).",
      "Lead with the hook — first line shows in the timeline.",
      "One idea per post; threads work better for depth.",
    ],
    linkedin: [
      "Aim for 1,300–2,000 characters for best engagement.",
      "Use line breaks — walls of text get skipped.",
      "End with a question to invite comments.",
    ],
  },
};