/**
 * Browser notifications + reminder scheduling.
 */

const Notifications = {
  async registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return null;
    try {
      return await navigator.serviceWorker.register("/static/sw.js");
    } catch (e) {
      console.warn("SW registration failed:", e);
      return null;
    }
  },

  async requestPermission() {
    if (!("Notification" in window)) return "unsupported";
    if (Notification.permission === "granted") return "granted";
    if (Notification.permission === "denied") return "denied";
    return await Notification.requestPermission();
  },

  _lastReminderDate: null,

  startReminderCheck() {
    if (!Settings.reminderEnabled) return;

    const check = () => {
      const now = new Date();
      const today = now.toDateString();
      const [h, m] = Settings.reminderTime.split(":").map(Number);
      if (now.getHours() === h && now.getMinutes() === m) {
        if (this._lastReminderDate !== today) {
          this._lastReminderDate = today;
          this.showReminder();
        }
      }
    };

    check();
    setInterval(check, 30_000);
  },

  async showReminder() {
    const title = "Daily Forge";
    const body = "Time to show up — what's one thing you'll share today?";

    if (Notification.permission === "granted") {
      if (navigator.serviceWorker?.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: "SHOW_REMINDER",
          title,
          body,
        });
      } else {
        new Notification(title, { body, tag: "daily-forge-reminder" });
      }
    }
  },
};