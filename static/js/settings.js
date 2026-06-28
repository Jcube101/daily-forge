/**
 * Settings — timezone, reminders, server sync.
 */

const Settings = {
  get timezone() {
    return localStorage.getItem("df-timezone") || Intl.DateTimeFormat().resolvedOptions().timeZone;
  },
  set timezone(v) {
    localStorage.setItem("df-timezone", v);
  },
  get reminderEnabled() {
    return localStorage.getItem("df-reminder-enabled") === "true";
  },
  set reminderEnabled(v) {
    localStorage.setItem("df-reminder-enabled", String(v));
  },
  get reminderTime() {
    return localStorage.getItem("df-reminder-time") || "18:00";
  },
  set reminderTime(v) {
    localStorage.setItem("df-reminder-time", v);
  },

  tzParam() {
    return `tz=${encodeURIComponent(this.timezone)}`;
  },

  async syncToServer() {
    await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        timezone: this.timezone,
        reminder_enabled: this.reminderEnabled,
        reminder_time: this.reminderTime,
      }),
    });
  },

  async loadFromServer() {
    const res = await fetch(`/api/settings?${this.tzParam()}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.timezone) this.timezone = data.timezone;
    this.reminderEnabled = data.reminder_enabled;
    this.reminderTime = data.reminder_time;
  },
};