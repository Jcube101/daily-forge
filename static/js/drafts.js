/**
 * Draft autosave — localStorage persistence.
 */

const Drafts = {
  KEYS: {
    single: "df-draft-single",
    thread: "df-draft-thread",
    threadItems: "df-draft-thread-items",
    platform: "df-draft-platform",
  },

  saveSingle(content) {
    localStorage.setItem(this.KEYS.single, content);
  },

  loadSingle() {
    return localStorage.getItem(this.KEYS.single) || "";
  },

  saveThread(formatted, items) {
    if (formatted) localStorage.setItem(this.KEYS.thread, formatted);
    if (items) localStorage.setItem(this.KEYS.threadItems, JSON.stringify(items));
  },

  loadThread() {
    return {
      formatted: localStorage.getItem(this.KEYS.thread) || "",
      items: JSON.parse(localStorage.getItem(this.KEYS.threadItems) || "[]"),
    };
  },

  savePlatform(platform) {
    localStorage.setItem(this.KEYS.platform, platform);
  },

  loadPlatform() {
    return localStorage.getItem(this.KEYS.platform) || "x";
  },

  clearSingle() {
    localStorage.removeItem(this.KEYS.single);
  },
};