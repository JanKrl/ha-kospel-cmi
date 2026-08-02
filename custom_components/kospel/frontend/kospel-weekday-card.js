/**
 * Kospel Weekday Schedule Assignment Card
 * Custom Lovelace Card for Home Assistant
 */

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
    this._statusMessage = null;
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
      title: "Kospel Weekday Schedule",
      schedule_type: "ch",
      ...config,
    };
    if (config.schedule_type) {
      this._scheduleType = config.schedule_type;
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
      title: "Kospel Weekday Schedule",
      device_id: deviceId,
      schedule_type: "ch",
    };
  }

  static getConfigElement() {
    return document.createElement("kospel-weekday-card-editor");
  }

  _getDeviceId() {
    if (this._config.device_id) return this._config.device_id;
    if (this._hass) {
      const dev = Object.values(this._hass.devices || {}).find(
        (d) => d.identifiers && d.identifiers.some(([domain]) => domain === "kospel")
      );
      if (dev) return dev.id;
    }
    return "";
  }

  async _loadSchedule() {
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
        service: "get_weekday_schedule",
        service_data: {
          device_id: deviceId,
          schedule_type: this._scheduleType,
        },
        return_response: true,
      });

      if (response && response.response) {
        this._schedule = { ...response.response };
        this._statusMessage = "Weekday schedule loaded successfully.";
      }
    } catch (err) {
      this._error = `Failed to load weekday schedule: ${err.message || err}`;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveSchedule() {
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
      await this._hass.callService("kospel", "set_weekday_schedule", {
        device_id: deviceId,
        schedule_type: this._scheduleType,
        ...this._schedule,
      });
      this._statusMessage = "Weekday schedule saved successfully!";
    } catch (err) {
      this._error = `Failed to save weekday schedule: ${err.message || err}`;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot) return;

    const title = this._config.title || "Kospel Weekday Schedule";
    const days = [
      { key: "monday", label: "Monday" },
      { key: "tuesday", label: "Tuesday" },
      { key: "wednesday", label: "Wednesday" },
      { key: "thursday", label: "Thursday" },
      { key: "friday", label: "Friday" },
      { key: "saturday", label: "Saturday" },
      { key: "sunday", label: "Sunday" },
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
          gap: 10px;
          margin-bottom: 20px;
        }
        .day-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 14px;
          border-radius: 8px;
          background: var(--secondary-background-color, #f9f9f9);
          border: 1px solid var(--divider-color, #e5e7eb);
        }
        .day-name {
          font-size: 14px;
          font-weight: 500;
        }
        .btn-row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
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
          <ha-icon icon="mdi:calendar-week"></ha-icon>
        </div>

        ${this._error ? `<div class="alert-error">${this._error}</div>` : ""}
        ${this._statusMessage ? `<div class="alert-success">${this._statusMessage}</div>` : ""}

        <div class="control-group">
          <label>Schedule Type</label>
          <select id="select-type">
            <option value="ch" ${this._scheduleType === "ch" ? "selected" : ""}>Central Heating (CH)</option>
            <option value="dhw" ${this._scheduleType === "dhw" ? "selected" : ""}>Hot Water (DHW)</option>
            <option value="circulation" ${this._scheduleType === "circulation" ? "selected" : ""}>Circulation</option>
          </select>
        </div>

        <div class="days-grid">
          ${days
            .map(
              (d) => `
              <div class="day-row">
                <span class="day-name">${d.label}</span>
                <select class="select-day-program" data-day="${d.key}">
                  ${[1, 2, 3, 4, 5, 6, 7, 8]
                    .map(
                      (p) => `
                    <option value="${p}" ${this._schedule[d.key] === p ? "selected" : ""}>
                      Program ${p}
                    </option>
                  `
                    )
                    .join("")}
                </select>
              </div>
            `
            )
            .join("")}
        </div>

        <div class="btn-row">
          <button type="button" class="btn-secondary" id="btn-load" ${this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:download"></ha-icon>'} Load Schedule
          </button>

          <button type="button" class="btn-primary" id="btn-save" ${this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:content-save"></ha-icon>'} Save Schedule
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

    // Load & Save buttons
    const btnLoad = root.querySelector("#btn-load");
    if (btnLoad) {
      btnLoad.addEventListener("click", () => this._loadSchedule());
    }

    const btnSave = root.querySelector("#btn-save");
    if (btnSave) {
      btnSave.addEventListener("click", () => this._saveSchedule());
    }

    // Day program select changes
    root.querySelectorAll(".select-day-program").forEach((select) => {
      select.addEventListener("change", (e) => {
        const day = e.target.dataset.day;
        this._schedule[day] = parseInt(e.target.value, 10);
        this._render();
      });
    });
  }
}

class KospelWeekdayCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.innerHTML = `
      <div style="padding: 12px; display: flex; flex-direction: column; gap: 12px;">
        <label style="font-size: 13px; font-weight: 500;">Title</label>
        <input type="text" id="editor-title" value="${config.title || "Kospel Weekday Schedule"}" style="padding: 8px; border-radius: 6px; border: 1px solid #ccc;">

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

if (!customElements.get("kospel-weekday-card")) {
  customElements.define("kospel-weekday-card", KospelWeekdayCard);
}
if (!customElements.get("kospel-weekday-card-editor")) {
  customElements.define("kospel-weekday-card-editor", KospelWeekdayCardEditor);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kospel-weekday-card",
  name: "Kospel Weekday Schedule Card",
  description: "Assign Kospel Daily Programs 1-8 to days of the week",
});
