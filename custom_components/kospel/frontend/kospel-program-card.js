/**
 * Kospel Daily Program Editor Card
 * Custom Lovelace Card for Home Assistant
 */

class KospelProgramCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._scheduleType = "ch";
    this._programId = 1;
    this._slots = [
      { start_minute: 0, stop_minute: 360, preset_id: 1 },
      { start_minute: 360, stop_minute: 1320, preset_id: 2 },
      { start_minute: 1320, stop_minute: 1440, preset_id: 1 },
    ];
    this._loading = false;
    this._error = null;
    this._statusMessage = null;
    this._activeSlotIndex = 0;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._render();
    }
  }

  setConfig(config) {
    this._config = {
      title: "Kospel Program Editor",
      schedule_type: "ch",
      program_id: 1,
      ...config,
    };
    if (config.schedule_type) {
      this._scheduleType = config.schedule_type;
    }
    if (config.program_id) {
      this._programId = parseInt(config.program_id, 10);
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
      title: "Kospel Program Editor",
      device_id: deviceId,
      schedule_type: "ch",
      program_id: 1,
    };
  }

  static getConfigElement() {
    return document.createElement("kospel-program-card-editor");
  }

  _getPresets() {
    if (this._scheduleType === "dhw") {
      return [
        { id: 0, label: "Off", color: "#6b7280", icon: "mdi:power" },
        { id: 1, label: "Eco", color: "#10b981", icon: "mdi:leaf" },
        { id: 2, label: "Comfort", color: "#f97316", icon: "mdi:water-boiler" },
      ];
    }
    if (this._scheduleType === "circulation") {
      return [
        { id: 0, label: "Off", color: "#6b7280", icon: "mdi:power" },
        { id: 1, label: "On", color: "#3b82f6", icon: "mdi:sync" },
      ];
    }
    // Default CH presets
    return [
      { id: 0, label: "Antifreeze", color: "#3b82f6", icon: "mdi:snowflake" },
      { id: 1, label: "Economy", color: "#10b981", icon: "mdi:thermometer-minus" },
      { id: 2, label: "Comfort", color: "#f97316", icon: "mdi:white-balance-sunny" },
      { id: 3, label: "Comfort+", color: "#ef4444", icon: "mdi:fire" },
      { id: 4, label: "Comfort-", color: "#34d399", icon: "mdi:thermometer-minus" },
    ];
  }

  _minuteToTime(min) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
  }

  _timeToMinute(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(":").map(Number);
    return (h || 0) * 60 + (m || 0);
  }

  _getPresetInfo(presetId) {
    const presets = this._getPresets();
    return presets.find((p) => p.id === presetId) || presets[0];
  }

  async _loadProgram() {
    if (!this._hass) return;
    const deviceId = this._getDeviceId();
    if (!deviceId) {
      this._error = "Please select a Kospel device in card options.";
      this._render();
      return;
    }

    this._loading = true;
    this._error = null;
    this._statusMessage = null;
    this._render();

    try {
      const response = await this._hass.callWS({
        type: "call_service",
        domain: "kospel",
        service: "get_program",
        service_data: {
          device_id: deviceId,
          schedule_type: this._scheduleType,
          program_id: this._programId,
        },
        return_response: true,
      });

      if (response && response.response && response.response.slots) {
        this._slots = response.response.slots;
        this._statusMessage = `Program ${this._programId} loaded successfully.`;
      }
    } catch (err) {
      this._error = `Failed to load program: ${err.message || err}`;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveProgram() {
    if (!this._hass) return;
    const deviceId = this._getDeviceId();
    if (!deviceId) {
      this._error = "Please select a Kospel device in card options.";
      this._render();
      return;
    }

    // Client-side validation
    for (let i = 0; i < this._slots.length; i++) {
      const slot = this._slots[i];
      if (slot.stop_minute <= slot.start_minute) {
        this._error = `Slot ${i + 1}: Stop time (${this._minuteToTime(slot.stop_minute)}) must be after start time (${this._minuteToTime(slot.start_minute)}).`;
        this._render();
        return;
      }
    }

    for (let i = 0; i < this._slots.length - 1; i++) {
      if (this._slots[i + 1].start_minute < this._slots[i].stop_minute) {
        this._error = `Slots ${i + 1} and ${i + 2} overlap!`;
        this._render();
        return;
      }
    }

    this._loading = true;
    this._error = null;
    this._statusMessage = null;
    this._render();

    try {
      await this._hass.callService("kospel", "set_program", {
        device_id: deviceId,
        schedule_type: this._scheduleType,
        program_id: this._programId,
        slots: this._slots,
      });
      this._statusMessage = `Program ${this._programId} saved successfully!`;
    } catch (err) {
      this._error = `Failed to save program: ${err.message || err}`;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _getDeviceId() {
    if (this._config.device_id) return this._config.device_id;
    // Fallback: pick first kospel device from registry
    if (this._hass) {
      const dev = Object.values(this._hass.devices || {}).find(
        (d) => d.identifiers && d.identifiers.some(([domain]) => domain === "kospel")
      );
      if (dev) return dev.id;
    }
    return "";
  }

  _addSlot() {
    if (this._slots.length >= 5) {
      this._error = "Maximum 5 time slots allowed per program.";
      this._render();
      return;
    }
    const lastStop = this._slots.length > 0 ? this._slots[this._slots.length - 1].stop_minute : 0;
    if (lastStop >= 1440) {
      this._error = "Cannot add slot: full 24h period covered.";
      this._render();
      return;
    }
    const newStop = Math.min(lastStop + 120, 1440);
    this._slots.push({
      start_minute: lastStop,
      stop_minute: newStop,
      preset_id: 1,
    });
    this._activeSlotIndex = this._slots.length - 1;
    this._render();
  }

  _removeSlot(index) {
    if (this._slots.length <= 1) {
      this._error = "Program must have at least 1 time slot.";
      this._render();
      return;
    }
    this._slots.splice(index, 1);
    this._activeSlotIndex = Math.max(0, index - 1);
    this._render();
  }

  _render() {
    if (!this.shadowRoot) return;

    const presets = this._getPresets();
    const title = this._config.title || "Kospel Program Editor";

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
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }
        .card-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }
        .controls-row {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
          flex-wrap: wrap;
        }
        .control-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
          flex: 1;
          min-width: 120px;
        }
        .control-group label {
          font-size: 12px;
          color: var(--secondary-text-color, #727272);
          font-weight: 500;
        }
        select, input[type="time"] {
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--secondary-background-color, #f9f9f9);
          color: var(--primary-text-color, #212121);
          font-size: 14px;
        }
        .timeline-container {
          margin: 20px 0;
          position: relative;
        }
        .timeline-bar {
          display: flex;
          height: 36px;
          border-radius: 8px;
          overflow: hidden;
          background: var(--secondary-background-color, #eee);
          touch-action: pan-y;
        }
        .timeline-segment {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          transition: filter 0.2s;
        }
        .timeline-segment:hover {
          filter: brightness(1.1);
        }
        .timeline-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 6px;
          font-size: 11px;
          color: var(--secondary-text-color, #727272);
        }
        .slots-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 16px;
        }
        .slot-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border-radius: 8px;
          background: var(--secondary-background-color, #f9f9f9);
          border: 1px solid var(--divider-color, #e5e7eb);
        }
        .slot-item.active {
          border-color: var(--primary-color, #3b82f6);
        }
        .slot-time {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .btn-row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-top: 16px;
        }
        button {
          padding: 10px 16px;
          border-radius: 8px;
          border: none;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .btn-primary {
          background: var(--primary-color, #3b82f6);
          color: #fff;
        }
        .btn-secondary {
          background: var(--secondary-background-color, #e5e7eb);
          color: var(--primary-text-color, #212121);
        }
        .btn-danger {
          background: #ef4444;
          color: #fff;
          padding: 6px 10px;
          font-size: 12px;
        }
        .alert-error {
          padding: 10px;
          background: #fee2e2;
          color: #991b1b;
          border-radius: 8px;
          font-size: 13px;
          margin-bottom: 12px;
        }
        .alert-success {
          padding: 10px;
          background: #d1fae5;
          color: #065f46;
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
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>

      <ha-card>
        <div class="card-header">
          <h2>${title}</h2>
          <ha-icon icon="mdi:calendar-clock"></ha-icon>
        </div>

        ${this._error ? `<div class="alert-error">${this._error}</div>` : ""}
        ${this._statusMessage ? `<div class="alert-success">${this._statusMessage}</div>` : ""}

        <div class="controls-row">
          <div class="control-group">
            <label>Schedule Type</label>
            <select id="select-type">
              <option value="ch" ${this._scheduleType === "ch" ? "selected" : ""}>Central Heating (CH)</option>
              <option value="dhw" ${this._scheduleType === "dhw" ? "selected" : ""}>Hot Water (DHW)</option>
              <option value="circulation" ${this._scheduleType === "circulation" ? "selected" : ""}>Circulation</option>
            </select>
          </div>

          <div class="control-group">
            <label>Program Number</label>
            <select id="select-program">
              ${[1, 2, 3, 4, 5, 6, 7, 8]
                .map((p) => `<option value="${p}" ${this._programId === p ? "selected" : ""}>Program ${p}</option>`)
                .join("")}
            </select>
          </div>
        </div>

        <div class="timeline-container">
          <div class="timeline-bar">
            ${this._slots
              .map((slot, idx) => {
                const duration = slot.stop_minute - slot.start_minute;
                const widthPct = ((duration / 1440) * 100).toFixed(2);
                const info = this._getPresetInfo(slot.preset_id);
                return `
                  <div class="timeline-segment" 
                       style="width: ${widthPct}%; background-color: ${info.color};"
                       title="${info.label}: ${this._minuteToTime(slot.start_minute)} - ${this._minuteToTime(slot.stop_minute)}"
                       data-idx="${idx}">
                    ${duration >= 120 ? info.label : ""}
                  </div>
                `;
              })
              .join("")}
          </div>
          <div class="timeline-labels">
            <span>00:00</span>
            <span>06:00</span>
            <span>12:00</span>
            <span>18:00</span>
            <span>24:00</span>
          </div>
        </div>

        <div class="slots-list">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="font-size: 14px;">Time Slots (${this._slots.length}/5)</strong>
            <button type="button" class="btn-secondary" id="btn-add-slot" style="padding: 6px 12px; font-size: 12px;">
              + Add Slot
            </button>
          </div>

          ${this._slots
            .map((slot, idx) => {
              const info = this._getPresetInfo(slot.preset_id);
              return `
                <div class="slot-item ${idx === this._activeSlotIndex ? "active" : ""}">
                  <div class="slot-time">
                    <input type="time" class="input-start" data-idx="${idx}" value="${this._minuteToTime(slot.start_minute)}">
                    <span>to</span>
                    <input type="time" class="input-stop" data-idx="${idx}" value="${this._minuteToTime(slot.stop_minute)}">
                  </div>

                  <select class="select-preset" data-idx="${idx}" style="flex: 1;">
                    ${presets
                      .map(
                        (p) =>
                          `<option value="${p.id}" ${slot.preset_id === p.id ? "selected" : ""}>${p.label}</option>`
                      )
                      .join("")}
                  </select>

                  <button type="button" class="btn-danger btn-remove" data-idx="${idx}">Remove</button>
                </div>
              `;
            })
            .join("")}
        </div>

        <div class="btn-row">
          <button type="button" class="btn-secondary" id="btn-load" ${this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:download"></ha-icon>'} Load Program
          </button>

          <button type="button" class="btn-primary" id="btn-save" ${this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:content-save"></ha-icon>'} Save Program
          </button>
        </div>
      </ha-card>
    `;

    this._attachEvents();
  }

  _attachEvents() {
    const root = this.shadowRoot;
    if (!root) return;

    // Type select
    const selectType = root.querySelector("#select-type");
    if (selectType) {
      selectType.addEventListener("change", (e) => {
        this._scheduleType = e.target.value;
        this._render();
      });
    }

    // Program select
    const selectProgram = root.querySelector("#select-program");
    if (selectProgram) {
      selectProgram.addEventListener("change", (e) => {
        this._programId = parseInt(e.target.value, 10);
        this._render();
      });
    }

    // Load & Save buttons
    const btnLoad = root.querySelector("#btn-load");
    if (btnLoad) {
      btnLoad.addEventListener("click", () => this._loadProgram());
    }

    const btnSave = root.querySelector("#btn-save");
    if (btnSave) {
      btnSave.addEventListener("click", () => this._saveProgram());
    }

    // Add slot
    const btnAdd = root.querySelector("#btn-add-slot");
    if (btnAdd) {
      btnAdd.addEventListener("click", () => this._addSlot());
    }

    // Remove slot buttons
    root.querySelectorAll(".btn-remove").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        this._removeSlot(idx);
      });
    });

    // Time input changes
    root.querySelectorAll(".input-start").forEach((input) => {
      input.addEventListener("change", (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        this._slots[idx].start_minute = this._timeToMinute(e.target.value);
        this._render();
      });
    });

    root.querySelectorAll(".input-stop").forEach((input) => {
      input.addEventListener("change", (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        this._slots[idx].stop_minute = this._timeToMinute(e.target.value);
        this._render();
      });
    });

    // Preset select changes
    root.querySelectorAll(".select-preset").forEach((select) => {
      select.addEventListener("change", (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        this._slots[idx].preset_id = parseInt(e.target.value, 10);
        this._render();
      });
    });
  }
}

class KospelProgramCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.innerHTML = `
      <div style="padding: 12px; display: flex; flex-direction: column; gap: 12px;">
        <label style="font-size: 13px; font-weight: 500;">Title</label>
        <input type="text" id="editor-title" value="${config.title || "Kospel Program Editor"}" style="padding: 8px; border-radius: 6px; border: 1px solid #ccc;">

        <label style="font-size: 13px; font-weight: 500;">Kospel Device ID</label>
        <input type="text" id="editor-device" value="${config.device_id || ""}" placeholder="Enter Kospel Device ID" style="padding: 8px; border-radius: 6px; border: 1px solid #ccc;">
      </div>
    `;
    this.querySelector("#editor-title").addEventListener("input", (e) => {
      this._config.title = e.target.value;
      this._fireConfigChanged();
    });
    this.querySelector("#editor-device").addEventListener("input", (e) => {
      this._config.device_id = e.target.value;
      this._fireConfigChanged();
    });
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

if (!customElements.get("kospel-program-card")) {
  customElements.define("kospel-program-card", KospelProgramCard);
}
if (!customElements.get("kospel-program-card-editor")) {
  customElements.define("kospel-program-card-editor", KospelProgramCardEditor);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kospel-program-card",
  name: "Kospel Daily Program Card",
  description: "View and edit Kospel heating daily time slots and presets",
});
