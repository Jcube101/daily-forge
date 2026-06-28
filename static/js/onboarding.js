/**
 * First-visit onboarding — welcome → timezone → first prompt.
 */

const Onboarding = {
  KEY: "df-onboarding-complete",

  isComplete() {
    return localStorage.getItem(this.KEY) === "true";
  },

  complete() {
    localStorage.setItem(this.KEY, "true");
    document.getElementById("onboarding-overlay")?.remove();
  },

  show() {
    if (this.isComplete()) return;

    const overlay = document.createElement("div");
    overlay.id = "onboarding-overlay";
    overlay.className = "onboarding-overlay";
    overlay.innerHTML = `
      <div class="onboarding-card" role="dialog" aria-labelledby="ob-title">
        <div class="onboarding-step active" data-step="1">
          <div class="onboarding-icon">🔥</div>
          <h2 id="ob-title">Welcome to Daily Forge</h2>
          <p>Build the habit of showing up on social media — one day at a time. No APIs, no pressure. Just consistency.</p>
          <button class="btn btn-primary ob-next">Get started</button>
        </div>
        <div class="onboarding-step" data-step="2">
          <div class="onboarding-icon">🌍</div>
          <h2>Set your timezone</h2>
          <p>Your streak resets at midnight in your local time.</p>
          <select id="ob-timezone" class="settings-select" aria-label="Timezone"></select>
          <button class="btn btn-primary ob-next">Continue</button>
        </div>
        <div class="onboarding-step" data-step="3">
          <div class="onboarding-icon">✍️</div>
          <h2>Your first prompt</h2>
          <p id="ob-prompt" class="prompt-text">Loading...</p>
          <p class="onboarding-hint">Write something, copy it to X or LinkedIn, then hit <strong>Mark as posted</strong>.</p>
          <button class="btn btn-primary ob-finish">Start forging</button>
        </div>
        <div class="onboarding-dots">
          <span class="dot active"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    this._populateTimezones();
    this._loadPrompt();
    this._bindEvents(overlay);
  },

  _populateTimezones() {
    const select = document.getElementById("ob-timezone");
    const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const zones = Intl.supportedValuesOf("timeZone");
    zones.forEach((z) => {
      const opt = document.createElement("option");
      opt.value = z;
      opt.textContent = z.replace(/_/g, " ");
      if (z === detected) opt.selected = true;
      select.appendChild(opt);
    });
  },

  async _loadPrompt() {
    const res = await fetch(`/api/prompt?tz=${encodeURIComponent(Settings.timezone)}`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("ob-prompt").textContent = data.prompt;
    }
  },

  _bindEvents(overlay) {
    let step = 1;
    const dots = overlay.querySelectorAll(".dot");
    const steps = overlay.querySelectorAll(".onboarding-step");

    const goTo = (n) => {
      step = n;
      steps.forEach((s) => s.classList.toggle("active", Number(s.dataset.step) === n));
      dots.forEach((d, i) => d.classList.toggle("active", i === n - 1));
    };

    overlay.querySelectorAll(".ob-next").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (step === 2) {
          Settings.timezone = document.getElementById("ob-timezone").value;
          await Settings.syncToServer();
          const tzSelect = document.getElementById("timezone-select");
          if (tzSelect) tzSelect.value = Settings.timezone;
        }
        goTo(step + 1);
      });
    });

    overlay.querySelector(".ob-finish")?.addEventListener("click", async () => {
      await Settings.syncToServer();
      this.complete();
      showToast("You're all set — show up today!");
    });
  },
};