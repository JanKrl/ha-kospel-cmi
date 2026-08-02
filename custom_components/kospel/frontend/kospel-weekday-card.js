const TRANSLATIONS = {
  en: {
    card_title_program: "Kospel Program Editor",
    card_title_weekday: "Kospel Weekday Schedule",
    schedule_type: "Schedule Type",
    program_number: "Program Number",
    ch: "Central Heating (CH)",
    dhw: "Hot Water (DHW)",
    circulation: "Circulation",
    program_n: "Program {n}",
    no_program: "No program",
    no_program_timeline: "No program assigned",
    cancel: "Cancel",
    save_schedule: "Save Schedule",
    schedule_saved: "Saved",
    unsaved_title: "Unsaved Changes",
    unsaved_body_weekday: "You have unsaved changes in your {type} weekday schedule. What would you like to do before switching?",
    save_and_switch: "Save & Switch",
    abandon_and_switch: "Abandon Changes & Switch",
    monday: "Monday",
    tuesday: "Tuesday",
    wednesday: "Wednesday",
    thursday: "Thursday",
    friday: "Friday",
    saturday: "Saturday",
    sunday: "Sunday",
    preset_off: "Off",
    preset_eco: "Eco",
    preset_comfort: "Comfort",
    preset_comfort_plus: "Comfort+",
    preset_comfort_minus: "Comfort-",
    preset_antifreeze: "Antifreeze",
    preset_economy: "Economy",
    preset_on: "On",
    failed_load_schedule: "Failed to load weekday schedule: {error}",
    failed_save_schedule: "Failed to save weekday schedule: {error}",
  },
  pl: {
    card_title_program: "Edytor programów Kospel",
    card_title_weekday: "Harmonogram tygodniowy Kospel",
    schedule_type: "Typ harmonogramu",
    program_number: "Numer programu",
    ch: "Centralne Ogrzewanie (CO)",
    dhw: "Ciepła Woda Użytkowa (CWU)",
    circulation: "Cyrkulacja",
    program_n: "Program {n}",
    no_program: "Brak programu",
    no_program_timeline: "Program jest pusty",
    cancel: "Anuluj",
    save_schedule: "Zapisz harmonogram",
    schedule_saved: "Zapisano",
    unsaved_title: "Niezapisane zmiany",
    unsaved_body_weekday: "Masz niezapisane zmiany w harmonogramie tygodniowym ({type}). Co chcesz zrobić przed przełączeniem?",
    save_and_switch: "Zapisz i przełącz",
    abandon_and_switch: "Odrzuć zmiany i przełącz",
    monday: "Poniedziałek",
    tuesday: "Wtorek",
    wednesday: "Środa",
    thursday: "Czwartek",
    friday: "Piątek",
    saturday: "Sobota",
    sunday: "Niedziela",
    preset_off: "Wyłączone",
    preset_eco: "Eko",
    preset_comfort: "Komfort",
    preset_comfort_plus: "Komfort+",
    preset_comfort_minus: "Komfort-",
    preset_antifreeze: "Ochrona przed zamarzaniem",
    preset_economy: "Ekonomiczny",
    preset_on: "Włączone",
    failed_load_schedule: "Nie udało się pobrać harmonogramu tygodniowego: {error}",
    failed_save_schedule: "Nie udało się zapisać harmonogramu tygodniowego: {error}",
  },
};

function localize(key, lang = "en", placeholders = {}) {
  const langKey = (lang || "en").toLowerCase().split("-")[0];
  const dict = TRANSLATIONS[langKey] || TRANSLATIONS.en;
  let text = dict[key] || TRANSLATIONS.en[key] || key;
  for (const [pKey, pVal] of Object.entries(placeholders)) {
    text = text.replace(new RegExp(`\\{${pKey}\\}`, "g"), pVal);
  }
  return text;
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "kospel-weekday-card")) {
  window.customCards.push({
    type: "kospel-weekday-card",
    name: "Kospel Weekday Schedule Card",
    description: "Assign Kospel Daily Programs 1-8 to days of the week",
  });
}

class KospelWeekdayCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._scheduleType = "ch";
    this._schedule = {
      monday: 1,
      tuesday: 1,
      wednesday: 1,
      thursday: 1,
      friday: 1,
      saturday: 2,
      sunday: 2,
    };
    this._loading = false;
    this._error = null;
    this._isSaved = false;
    this._errorTimer = null;
    this._hasUnsavedChanges = false;
    this._confirmModalOpen = false;
    this._pendingSwitch = null;
    this._initialized = false;
    this._programs = {};
  }

  _getPresets() {
    if (this._scheduleType === "dhw") {
      return [
        { id: 0, name: this._t("preset_off"), color: "#6b7280", icon: "mdi:power" },
        { id: 1, name: this._t("preset_economy"), color: "#10b981", icon: "mdi:leaf" },
        { id: 2, name: this._t("preset_comfort"), color: "#f97316", icon: "mdi:thermometer" },
      ];
    }
    if (this._scheduleType === "circulation") {
      return [
        { id: 0, name: this._t("preset_off"), color: "#6b7280", icon: "mdi:power" },
        { id: 1, name: this._t("preset_on"), color: "#3b82f6", icon: "mdi:sync" },
      ];
    }
    // Default CH presets
    return [
      { id: 0, name: this._t("preset_antifreeze"), color: "#3b82f6", icon: "mdi:snowflake" },
      { id: 1, name: this._t("preset_economy"), color: "#10b981", icon: "mdi:leaf" },
      { id: 2, name: this._t("preset_comfort"), color: "#f97316", icon: "mdi:thermometer" },
      { id: 3, name: this._t("preset_comfort_plus"), color: "#ef4444", icon: "mdi:thermometer-plus" },
      { id: 4, name: this._t("preset_comfort_minus"), color: "#facc15", icon: "mdi:thermometer-minus" },
    ];
  }

  _getPresetInfo(presetId) {
    const presets = this._getPresets();
    return presets.find((p) => p.id === presetId) || presets[0];
  }

  _minuteToDisplayTime(min) {
    if (min >= 1440) return "24:00";
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
  }

  _getBoundaryLabels(slots) {
    if (!slots || slots.length === 0) {
      return [
        { label: "00:00", pct: 0, align: "left" },
        { label: "24:00", pct: 100, align: "right" },
      ];
    }

    const points = [];
    points.push({ min: 0, label: "00:00" });

    const sortedSlots = [...slots].sort((a, b) => a.start_minute - b.start_minute);
    for (let i = 0; i < sortedSlots.length; i++) {
      const s = sortedSlots[i];
      if (s.start_minute > 0 && s.start_minute < 1440) {
        points.push({ min: s.start_minute, label: this._minuteToDisplayTime(s.start_minute) });
      }
      if (s.stop_minute > 0 && s.stop_minute < 1440) {
        points.push({ min: s.stop_minute, label: this._minuteToDisplayTime(s.stop_minute) });
      }
    }

    points.push({ min: 1440, label: "24:00" });

    // Deduplicate exact timestamps
    const uniquePoints = [];
    points.forEach((p) => {
      if (!uniquePoints.some((u) => u.min === p.min)) {
        uniquePoints.push(p);
      }
    });

    uniquePoints.sort((a, b) => a.min - b.min);

    // Anti-collision algorithm: ensure minimum gap between labels is 120 minutes (~32px)
    // Always include 00:00 and 24:00. Skip intermediate labels if too close to previous or end label.
    const result = [];
    const MIN_GAP_MINUTES = 120;

    result.push(uniquePoints[0]);

    for (let i = 1; i < uniquePoints.length - 1; i++) {
      const candidate = uniquePoints[i];
      const prev = result[result.length - 1];
      const endPoint = uniquePoints[uniquePoints.length - 1];

      if (candidate.min - prev.min >= MIN_GAP_MINUTES && endPoint.min - candidate.min >= MIN_GAP_MINUTES) {
        result.push(candidate);
      }
    }

    if (uniquePoints.length > 1) {
      result.push(uniquePoints[uniquePoints.length - 1]);
    }

    return result.map((p) => {
      const pct = ((p.min / 1440) * 100).toFixed(2);
      let align = "center";
      if (p.min <= 60) align = "left";
      else if (p.min >= 1380) align = "right";
      return { label: p.label, pct, align };
    });
  }

  _getLang() {
    if (this._config && this._config.language) {
      return this._config.language;
    }
    if (this._hass) {
      return this._hass.language || (this._hass.locale && this._hass.locale.language) || "en";
    }
    return "en";
  }

  _t(key, placeholders = {}) {
    return localize(key, this._getLang(), placeholders);
  }

  _setError(msg) {
    this._error = msg;
    if (this._errorTimer) clearTimeout(this._errorTimer);
    if (msg) {
      this._errorTimer = setTimeout(() => {
        this._error = null;
        this._render();
      }, 4000);
    }
  }

  _markUnsaved() {
    this._hasUnsavedChanges = true;
    this._isSaved = false;
    this._error = null;
  }

  set hass(hass) {
    const isFirstHass = !this._hass && hass;
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._render();
      if (isFirstHass) {
        this._loadSchedule();
      }
    }
  }

  async _performSwitch(newType) {
    this._confirmModalOpen = false;
    this._pendingSwitch = null;
    this._scheduleType = newType;
    this._hasUnsavedChanges = false;
    this._isSaved = false;
    this._render();

    await this._loadSchedule();
  }

  getCardSize() {
    return 4;
  }

  setConfig(config) {
    this._config = {
      title: "",
      schedule_type: "ch",
      ...(config || {}),
    };
    if (this._config.schedule_type) {
      this._scheduleType = this._config.schedule_type;
    }
    this._render();
  }

  static getStubConfig(hass) {
    let deviceId = "";
    if (hass) {
      const kospelEntity = Object.values(hass.states).find(
        (e) => e.entity_id.startsWith("climate.kospel") || e.entity_id.startsWith("climate.heater")
      );
      if (kospelEntity) {
        deviceId = kospelEntity.entity_id;
      }
    }
    return {
      title: "",
      device_id: deviceId,
      schedule_type: "ch",
    };
  }

  static getConfigElement() {
    return document.createElement("kospel-weekday-card-editor");
  }

  _getDeviceId() {
    if (this._config && this._config.device_id) return this._config.device_id;
    if (this._hass && this._hass.states) {
      const kospelEntity = Object.values(this._hass.states).find(
        (e) => e.entity_id.startsWith("climate.kospel") || e.entity_id.startsWith("climate.heater")
      );
      if (kospelEntity) return kospelEntity.entity_id;
    }
    return "";
  }

  async _loadSchedule() {
    if (!this._hass) return;
    const deviceId = this._getDeviceId();

    this._loading = true;
    this._error = null;
    this._render();

    try {
      const serviceData = {
        schedule_type: this._scheduleType,
      };
      if (deviceId) {
        serviceData.device_id = deviceId;
      }

      const response = await this._hass.callWS({
        type: "call_service",
        domain: "kospel",
        service: "get_weekday_schedule",
        service_data: serviceData,
        return_response: true,
      });

      if (response && response.response) {
        this._schedule = { ...response.response };
        this._isSaved = true;
        this._hasUnsavedChanges = false;
      }

      // Fetch all 8 programs for the active schedule type
      const programPromises = [1, 2, 3, 4, 5, 6, 7, 8].map(async (progId) => {
        try {
          const res = await this._hass.callWS({
            type: "call_service",
            domain: "kospel",
            service: "get_program",
            service_data: {
              schedule_type: this._scheduleType,
              program_id: progId,
              ...(deviceId ? { device_id: deviceId } : {}),
            },
            return_response: true,
          });
          if (res && res.response && Array.isArray(res.response.slots)) {
            return { progId, slots: res.response.slots };
          }
        } catch (err) {}
        return { progId, slots: [] };
      });

      const programResults = await Promise.all(programPromises);
      this._programs = {};
      programResults.forEach(({ progId, slots }) => {
        this._programs[progId] = slots;
      });
    } catch (err) {
      this._setError(this._t("failed_load_schedule", { error: err.message || err }));
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveSchedule() {
    if (!this._hass) return false;
    const deviceId = this._getDeviceId();

    this._loading = true;
    this._error = null;
    this._render();

    try {
      const serviceData = {
        schedule_type: this._scheduleType,
        ...this._schedule,
      };
      if (deviceId) {
        serviceData.device_id = deviceId;
      }

      await this._hass.callService("kospel", "set_weekday_schedule", serviceData);
      this._isSaved = true;
      this._hasUnsavedChanges = false;
      return true;
    } catch (err) {
      this._isSaved = false;
      this._setError(this._t("failed_save_schedule", { error: err.message || err }));
      return false;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot) return;

    const days = [
      { key: "monday", label: this._t("monday") },
      { key: "tuesday", label: this._t("tuesday") },
      { key: "wednesday", label: this._t("wednesday") },
      { key: "thursday", label: this._t("thursday") },
      { key: "friday", label: this._t("friday") },
      { key: "saturday", label: this._t("saturday") },
      { key: "sunday", label: this._t("sunday") },
    ];

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #212121);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
        }
        .control-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
          margin-bottom: 16px;
        }
        .control-group label {
          font-size: 12px;
          color: var(--secondary-text-color, #727272);
          font-weight: 500;
        }
        select {
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--secondary-background-color, #f9f9f9);
          color: var(--primary-text-color, #212121);
          font-size: 14px;
        }
        .days-grid {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 20px;
        }
        .day-card {
          background: var(--secondary-background-color, #f8fafc);
          border: 1px solid var(--divider-color, #e2e8f0);
          border-radius: 10px;
          padding: 12px 14px;
        }
        .day-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        .day-name {
          font-size: 14px;
          font-weight: 700;
          color: var(--primary-text-color, #1e293b);
        }
        .select-day-program {
          padding: 6px 10px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #cbd5e1);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #1e293b);
          font-size: 13px;
          font-weight: 500;
        }
        .day-timeline-container {
          position: relative;
          margin-top: 4px;
        }
        .day-timeline-bar {
          position: relative;
          height: 22px;
          background: var(--secondary-background-color, #e2e8f0);
          border-radius: 6px;
          overflow: hidden;
          display: flex;
          align-items: center;
        }
        .day-timeline-segment {
          height: 100%;
          position: absolute;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 10px;
          box-sizing: border-box;
          border-right: 1px solid rgba(255,255,255,0.2);
          overflow: hidden;
        }
        .day-timeline-segment ha-icon {
          --mdc-icon-size: 14px;
          filter: drop-shadow(0 1px 2px rgba(0,0,0,0.4));
          pointer-events: none;
        }
        .day-timeline-labels {
          position: relative;
          height: 16px;
          margin-top: 3px;
          font-size: 10px;
          font-weight: 500;
          color: var(--secondary-text-color, #64748b);
        }
        .day-label-item {
          position: absolute;
          top: 0;
          white-space: nowrap;
        }
        button {
          border: none;
          border-radius: 8px;
          font-family: inherit;
          font-weight: 600;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          box-sizing: border-box;
        }
        .btn-row {
          display: flex;
          gap: 12px;
          margin-top: 16px;
          width: 100%;
        }
        .btn-row button {
          flex: 1;
          justify-content: center;
          height: 40px;
          padding: 0 16px;
          font-size: 14px;
          white-space: nowrap;
          min-width: 0;
        }
        .btn-primary {
          background: var(--primary-color, #3b82f6);
          color: #fff;
        }
        .btn-success {
          background: #10b981;
          color: #fff;
        }
        .btn-secondary {
          background: var(--secondary-background-color, #e5e7eb);
          color: var(--primary-text-color, #212121);
        }
        .btn-danger {
          background: #ef4444;
          color: #fff;
        }
        .alert-error {
          padding: 10px;
          background: #fee2e2;
          color: #991b1b;
          border-radius: 8px;
          font-size: 13px;
          margin-bottom: 12px;
        }
        .spinner {
          border: 2px solid rgba(255,255,255,0.3);
          border-radius: 50%;
          border-top: 2px solid #fff;
          width: 14px;
          height: 14px;
          animation: spin 0.8s linear infinite;
        }
        .confirm-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.15s ease-out;
        }
        .confirm-modal-dialog {
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #1e293b);
          border-radius: 16px;
          padding: 20px;
          width: 340px;
          max-width: 90vw;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .confirm-modal-title {
          font-size: 16px;
          font-weight: 700;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .confirm-modal-body {
          font-size: 14px;
          color: var(--secondary-text-color, #64748b);
          line-height: 1.5;
        }
        .confirm-modal-actions {
          display: flex;
          flex-direction: column;
          gap: 8px;
          width: 100%;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.96); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>

      <ha-card>
        ${this._error ? `<div class="alert-error">${this._error}</div>` : ""}

        <div class="control-group">
          <label>${this._t("schedule_type")}</label>
          <select id="select-type">
            <option value="ch" ${this._scheduleType === "ch" ? "selected" : ""}>${this._t("ch")}</option>
            <option value="dhw" ${this._scheduleType === "dhw" ? "selected" : ""}>${this._t("dhw")}</option>
            <option value="circulation" ${this._scheduleType === "circulation" ? "selected" : ""}>${this._t("circulation")}</option>
          </select>
        </div>

        <div class="days-grid">
          ${days
            .map((d) => {
              const progId = parseInt(this._schedule[d.key], 10) || 1;
              const slots = (this._programs && this._programs[progId]) || [];
              const boundaryLabels = this._getBoundaryLabels(slots);

              return `
                <div class="day-card">
                  <div class="day-header">
                    <span class="day-name">${d.label}</span>
                    <select class="select-day-program" data-day="${d.key}">
                      ${[1, 2, 3, 4, 5, 6, 7, 8]
                        .map(
                          (p) => `
                        <option value="${p}" ${progId === p ? "selected" : ""}>
                          ${this._t("program_n", { n: p })}
                        </option>
                      `
                        )
                        .join("")}
                    </select>
                  </div>

                  ${
                    slots.length === 0
                      ? `
                        <div class="day-timeline-container">
                          <div class="day-timeline-bar">
                            <div style="width: 100%; text-align: center; font-size: 11px; font-weight: 500; color: var(--secondary-text-color, #64748b);">
                              ${this._t("program_n", { n: progId })} (${this._t("no_program_timeline")})
                            </div>
                          </div>
                          <div class="day-timeline-labels">
                            <span class="day-label-item" style="left: 0%;">00:00</span>
                            <span class="day-label-item" style="right: 0%;">24:00</span>
                          </div>
                        </div>
                      `
                      : `
                        <div class="day-timeline-container">
                          <div class="day-timeline-bar">
                            ${slots
                              .map((slot) => {
                                const duration = slot.stop_minute - slot.start_minute;
                                const leftPct = ((slot.start_minute / 1440) * 100).toFixed(2);
                                const widthPct = ((duration / 1440) * 100).toFixed(2);
                                const info = this._getPresetInfo(slot.preset_id);
                                return `
                                  <div class="day-timeline-segment" 
                                       style="left: ${leftPct}%; width: ${widthPct}%; background-color: ${info.color};"
                                       title="${info.name}: ${this._minuteToDisplayTime(slot.start_minute)} - ${this._minuteToDisplayTime(slot.stop_minute)}">
                                    ${duration >= 60 ? `<ha-icon icon="${info.icon}"></ha-icon>` : ""}
                                  </div>
                                `;
                              })
                              .join("")}
                          </div>
                          <div class="day-timeline-labels">
                            ${boundaryLabels
                              .map((lbl) => {
                                if (lbl.align === "left") {
                                  return `<span class="day-label-item" style="left: 0%;">${lbl.label}</span>`;
                                }
                                if (lbl.align === "right") {
                                  return `<span class="day-label-item" style="right: 0%;">${lbl.label}</span>`;
                                }
                                return `<span class="day-label-item" style="left: ${lbl.pct}%; transform: translateX(-50%);">${lbl.label}</span>`;
                              })
                              .join("")}
                          </div>
                        </div>
                      `
                  }
                </div>
              `;
            })
            .join("")}
        </div>

        <div class="btn-row">
          <button type="button" class="${this._hasUnsavedChanges ? "btn-danger" : "btn-secondary"}" id="btn-cancel" ${!this._hasUnsavedChanges || this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:close"></ha-icon>'} ${this._t("cancel")}
          </button>

          ${
            this._hasUnsavedChanges
              ? `<button type="button" class="btn-success" id="btn-save" ${this._loading ? "disabled" : ""}>
                   ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:content-save"></ha-icon>'} ${this._t("save_schedule")}
                 </button>`
              : `<button type="button" class="btn-primary" id="btn-save" ${this._loading ? "disabled" : ""}>
                   <ha-icon icon="mdi:check"></ha-icon> ${this._t("schedule_saved")}
                 </button>`
          }
        </div>
      </ha-card>

      ${this._confirmModalOpen ? `
        <div class="confirm-modal-overlay">
          <div class="confirm-modal-dialog">
            <div class="confirm-modal-title">
              <ha-icon icon="mdi:alert-circle-outline" style="color: #f59e0b;"></ha-icon>
              <span>${this._t("unsaved_title")}</span>
            </div>
            <div class="confirm-modal-body">
              ${this._t("unsaved_body_weekday", { type: this._t(this._scheduleType) })}
            </div>
            <div class="confirm-modal-actions">
              <button type="button" class="btn-primary" id="btn-modal-save" style="justify-content: center;">
                <ha-icon icon="mdi:content-save"></ha-icon> ${this._t("save_and_switch")}
              </button>
              <button type="button" class="btn-danger" id="btn-modal-abandon" style="justify-content: center; padding: 10px 16px; font-size: 14px;">
                <ha-icon icon="mdi:delete-outline"></ha-icon> ${this._t("abandon_and_switch")}
              </button>
              <button type="button" class="btn-secondary" id="btn-modal-cancel" style="justify-content: center;">
                ${this._t("cancel")}
              </button>
            </div>
          </div>
        </div>
      ` : ""}
    `;

    this._attachEvents();
  }

  _attachEvents() {
    const root = this.shadowRoot;
    if (!root) return;

    // Type select with unsaved changes prompt & auto-fetch
    const selectType = root.querySelector("#select-type");
    if (selectType) {
      selectType.addEventListener("change", (e) => {
        const newType = e.target.value;
        if (newType === this._scheduleType) return;

        if (this._hasUnsavedChanges) {
          selectType.value = this._scheduleType;
          this._pendingSwitch = newType;
          this._confirmModalOpen = true;
          this._render();
        } else {
          this._performSwitch(newType);
        }
      });
    }

    // Unsaved changes modal button handlers
    if (this._confirmModalOpen) {
      const btnModalSave = root.querySelector("#btn-modal-save");
      if (btnModalSave) {
        btnModalSave.addEventListener("click", async () => {
          this._confirmModalOpen = false;
          const success = await this._saveSchedule();
          if (success !== false && this._pendingSwitch) {
            await this._performSwitch(this._pendingSwitch);
          }
        });
      }

      const btnModalAbandon = root.querySelector("#btn-modal-abandon");
      if (btnModalAbandon) {
        btnModalAbandon.addEventListener("click", async () => {
          this._confirmModalOpen = false;
          if (this._pendingSwitch) {
            await this._performSwitch(this._pendingSwitch);
          }
        });
      }

      const btnModalCancel = root.querySelector("#btn-modal-cancel");
      if (btnModalCancel) {
        btnModalCancel.addEventListener("click", () => {
          this._confirmModalOpen = false;
          this._pendingSwitch = null;
          this._render();
        });
      }
    }

    // Cancel & Save buttons
    const btnCancel = root.querySelector("#btn-cancel");
    if (btnCancel) {
      btnCancel.addEventListener("click", () => {
        if (this._hasUnsavedChanges) {
          this._loadSchedule();
        }
      });
    }

    const btnSave = root.querySelector("#btn-save");
    if (btnSave) {
      btnSave.addEventListener("click", () => this._saveSchedule());
    }

    // Day program select changes
    root.querySelectorAll(".select-day-program").forEach((select) => {
      select.addEventListener("change", (e) => {
        this._markUnsaved();
        const day = e.target.dataset.day;
        this._schedule[day] = parseInt(e.target.value, 10);
        this._render();
      });
    });
  }
}

class KospelWeekdayCardEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;

    const schema = [
      {
        name: "device_id",
        selector: {
          device: {
            filter: { integration: "kospel" }
          }
        }
      },
    ];

    if (!this._haForm) {
      this.innerHTML = "";
      this._haForm = document.createElement("ha-form");
      this._haForm.addEventListener("value-changed", (ev) => {
        this._config = { ...this._config, ...ev.detail.value };
        this._fireConfigChanged();
      });
      this.appendChild(this._haForm);
    }

    this._haForm.hass = this._hass;
    this._haForm.data = {
      ...this._config,
    };
    this._haForm.schema = schema;
    this._haForm.computeLabel = (schema) => {
      if (schema.name === "device_id") return "Kospel Device";
      return schema.name;
    };
  }

  _fireConfigChanged() {
    const event = new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

if (!customElements.get("kospel-weekday-card")) {
  customElements.define("kospel-weekday-card", KospelWeekdayCard);
}
if (!customElements.get("kospel-weekday-card-editor")) {
  customElements.define("kospel-weekday-card-editor", KospelWeekdayCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "kospel-weekday-card")) {
  window.customCards.push({
    type: "kospel-weekday-card",
    name: "Kospel Weekday Schedule Card",
    description: "Assign Kospel Daily Programs 1-8 to days of the week",
  });
}

// Automatically trigger Lovelace dashboard rebuild and self-heal any temporary error cards
function forceLovelaceRebuild() {
  window.dispatchEvent(new CustomEvent("ll-rebuild"));
  window.dispatchEvent(new Event("location-changed"));

  try {
    const root = document.querySelector("home-assistant")?.shadowRoot
      ?.querySelector("home-assistant-main")?.shadowRoot
      ?.querySelector("ha-drawer")
      ?.querySelector("partial-panel-resolver")
      ?.querySelector("ha-panel-lovelace")?.shadowRoot
      ?.querySelector("hui-root")?.shadowRoot;

    if (root) {
      const errorCards = root.querySelectorAll("hui-error-card, hui-card-element-editor");
      errorCards.forEach((card) => {
        if (card.textContent && card.textContent.includes("kospel-weekday-card")) {
          const parent = card.parentElement;
          const config = card._config;
          if (parent && config) {
            const newCard = document.createElement("kospel-weekday-card");
            if (typeof newCard.setConfig === "function") {
              newCard.setConfig(config);
              if (card.hass) newCard.hass = card.hass;
              parent.replaceChild(newCard, card);
            }
          }
        }
      });
    }
  } catch (err) {}
}

forceLovelaceRebuild();
setTimeout(forceLovelaceRebuild, 50);
setTimeout(forceLovelaceRebuild, 250);
setTimeout(forceLovelaceRebuild, 1000);
