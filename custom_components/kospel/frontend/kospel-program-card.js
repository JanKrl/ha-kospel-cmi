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
    time_slots: "Time Slots ({current}/{max})",
    add_slot: "+ Add Slot",
    remove: "Remove",
    to: "to",
    cancel: "Cancel",
    save_program: "Save Program",
    program_saved: "Saved",
    save_schedule: "Save Schedule",
    schedule_saved: "Saved",
    unsaved_title: "Unsaved Changes",
    unsaved_body_program: "You have unsaved changes in Program {program} ({type}). What would you like to do before switching?",
    unsaved_body_weekday: "You have unsaved changes in your {type} weekday schedule. What would you like to do before switching?",
    save_and_switch: "Save & Switch",
    abandon_and_switch: "Abandon Changes & Switch",
    drag_start_time: "Drag start time ({time})",
    drag_boundary: "Drag boundary ({time})",
    drag_end_time: "Drag end time ({time})",
    preset_off: "Off",
    preset_eco: "Eco",
    preset_comfort: "Comfort",
    preset_comfort_plus: "Comfort+",
    preset_comfort_minus: "Comfort-",
    preset_antifreeze: "Antifreeze",
    preset_economy: "Economy",
    preset_on: "On",
    monday: "Monday",
    tuesday: "Tuesday",
    wednesday: "Wednesday",
    thursday: "Thursday",
    friday: "Friday",
    saturday: "Saturday",
    sunday: "Sunday",
    max_slots_error: "Maximum 5 time slots allowed per program.",
    slot_stop_before_start_error: "Slot {slot}: Stop time ({stop}) must be strictly after start time ({start}).",
    slot_gap_error: "Slot {nextSlot} must start at least 1 minute after Slot {slot} ends! Slot {slot} ends at {stop}, so Slot {nextSlot} must start at {nextStart} or later.",
    failed_load_program: "Failed to load program: {error}",
    failed_save_program: "Failed to save program: {error}",
    failed_load_schedule: "Failed to load weekday schedule: {error}",
    failed_save_schedule: "Failed to save weekday schedule: {error}",
    empty_program_title: "Program {n} is empty",
    empty_program_info: "Click '+ Add Slot' or empty space on timeline to start.",
    empty_program_timeline: "No active time slots — Click to add",
    add_slot_here: "Add slot",
    click_to_add_slot: "Click empty space to add a time slot here",
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
    time_slots: "Przedziały czasowe ({current}/{max})",
    add_slot: "+ Dodaj przedział",
    remove: "Usuń",
    to: "do",
    cancel: "Anuluj",
    save_program: "Zapisz program",
    program_saved: "Zapisano",
    save_schedule: "Zapisz harmonogram",
    schedule_saved: "Zapisano",
    unsaved_title: "Niezapisane zmiany",
    unsaved_body_program: "Masz niezapisane zmiany w Programie {program} ({type}). Co chcesz zrobić przed przełączeniem?",
    unsaved_body_weekday: "Masz niezapisane zmiany w harmonogramie tygodniowym ({type}). Co chcesz zrobić przed przełączeniem?",
    save_and_switch: "Zapisz i przełącz",
    abandon_and_switch: "Odrzuć zmiany i przełącz",
    drag_start_time: "Przeciągnij czas rozpoczęcia ({time})",
    drag_boundary: "Przeciągnij granicę ({time})",
    drag_end_time: "Przeciągnij czas zakończenia ({time})",
    preset_off: "Wyłączone",
    preset_eco: "Eko",
    preset_comfort: "Komfort",
    preset_comfort_plus: "Komfort+",
    preset_comfort_minus: "Komfort-",
    preset_antifreeze: "Ochrona przed zamarzaniem",
    preset_economy: "Ekonomiczny",
    preset_on: "Włączone",
    monday: "Poniedziałek",
    tuesday: "Wtorek",
    wednesday: "Środa",
    thursday: "Czwartek",
    friday: "Piątek",
    saturday: "Sobota",
    sunday: "Niedziela",
    max_slots_error: "Maksymalnie 5 przedziałów czasowych na program.",
    slot_stop_before_start_error: "Przedział {slot}: Czas zakończenia ({stop}) musi być późniejszy niż czas rozpoczęcia ({start}).",
    slot_gap_error: "Przedział {nextSlot} musi rozpoczynać się co najmniej 1 minutę po zakończeniu Przedziału {slot}! Przedział {slot} kończy się o {stop}, więc Przedział {nextSlot} musi zaczynać się o {nextStart} lub później.",
    failed_load_program: "Nie udało się pobrać programu: {error}",
    failed_save_program: "Nie udało się zapisać programu: {error}",
    failed_load_schedule: "Nie udało się pobrać harmonogramu tygodniowego: {error}",
    failed_save_schedule: "Nie udało się zapisać harmonogramu tygodniowego: {error}",
    empty_program_title: "Program {n} jest pusty",
    empty_program_info: "Kliknij „+ Dodaj przedział” lub wolne miejsce na osią czasu, aby rozpocząć.",
    empty_program_timeline: "Brak aktywnych przedziałów — Kliknij, aby dodać",
    add_slot_here: "Dodaj przedział",
    click_to_add_slot: "Kliknij w wolne miejsce, aby dodać przedział",
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
if (!window.customCards.some((c) => c.type === "kospel-program-card")) {
  window.customCards.push({
    type: "kospel-program-card",
    name: "Kospel Daily Program Card",
    description: "View and edit Kospel heating daily time slots and presets",
  });
}

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
    this._isSaved = false;
    this._errorTimer = null;
    this._activeSlotIndex = 0;
    this._hasUnsavedChanges = false;
    this._confirmModalOpen = false;
    this._pendingSwitch = null;
    this._initialized = false;
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
        this._loadProgram();
      }
    }
  }

  async _performSwitch(newType, newProgramId) {
    this._confirmModalOpen = false;
    this._pendingSwitch = null;
    this._scheduleType = newType;
    this._programId = newProgramId;
    this._hasUnsavedChanges = false;
    this._isSaved = false;
    this._render();

    await this._loadProgram();
  }

  getCardSize() {
    return 5;
  }

  setConfig(config) {
    this._config = {
      title: "",
      schedule_type: "ch",
      program_id: 1,
      sliding_precision: 5,
      ...(config || {}),
    };
    if (this._config.schedule_type) {
      this._scheduleType = this._config.schedule_type;
    }
    if (this._config.program_id) {
      const pId = parseInt(this._config.program_id, 10);
      if (!isNaN(pId)) {
        this._programId = pId;
      }
    }
    const prec = parseInt(this._config.sliding_precision, 10);
    this._slidingPrecision = isNaN(prec) ? 5 : Math.max(1, Math.min(60, prec));
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
      program_id: 1,
      sliding_precision: 5,
    };
  }

  static getConfigElement() {
    return document.createElement("kospel-program-card-editor");
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
    // Default CH presets matching Kospel UI motifs
    return [
      { id: 0, name: this._t("preset_antifreeze"), color: "#3b82f6", icon: "mdi:snowflake" },
      { id: 1, name: this._t("preset_economy"), color: "#10b981", icon: "mdi:leaf" },
      { id: 2, name: this._t("preset_comfort"), color: "#f97316", icon: "mdi:thermometer" },
      { id: 3, name: this._t("preset_comfort_plus"), color: "#ef4444", icon: "mdi:thermometer-plus" },
      { id: 4, name: this._t("preset_comfort_minus"), color: "#facc15", icon: "mdi:thermometer-minus" },
    ];
  }

  _minuteToTime(min) {
    if (min >= 1440) return "23:59";
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
  }

  _minuteToDisplayTime(min) {
    if (min >= 1440) return "24:00";
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
  }

  _timeToMinute(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(":").map(Number);
    if (h === 23 && m === 59) return 1440;
    return (h || 0) * 60 + (m || 0);
  }

  _getPresetInfo(presetId) {
    const presets = this._getPresets();
    return presets.find((p) => p.id === presetId) || presets[0];
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

  async _loadProgram() {
    if (!this._hass) return;
    const deviceId = this._getDeviceId();

    this._loading = true;
    this._error = null;
    this._render();

    try {
      const serviceData = {
        schedule_type: this._scheduleType,
        program_id: this._programId,
      };
      if (deviceId) {
        serviceData.device_id = deviceId;
      }

      const response = await this._hass.callWS({
        type: "call_service",
        domain: "kospel",
        service: "get_program",
        service_data: serviceData,
        return_response: true,
      });

      if (response && response.response && Array.isArray(response.response.slots)) {
        const validSlots = response.response.slots.filter(
          (s) =>
            s &&
            typeof s.start_minute === "number" &&
            typeof s.stop_minute === "number" &&
            s.start_minute >= 0 &&
            s.stop_minute > s.start_minute &&
            s.start_minute <= 1440
        );
        this._slots = validSlots;
        this._isSaved = true;
        this._hasUnsavedChanges = false;
      }
    } catch (err) {
      this._setError(this._t("failed_load_program", { error: err.message || err }));
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveProgram() {
    if (!this._hass) return false;
    const deviceId = this._getDeviceId();

    // Client-side validation
    for (let i = 0; i < this._slots.length; i++) {
      const slot = this._slots[i];
      if (slot.stop_minute <= slot.start_minute) {
        this._setError(this._t("slot_stop_before_start_error", {
          slot: i + 1,
          stop: this._minuteToTime(slot.stop_minute),
          start: this._minuteToTime(slot.start_minute),
        }));
        this._render();
        return false;
      }
    }

    // Sort slots by start_minute
    this._slots.sort((a, b) => a.start_minute - b.start_minute);

    for (let i = 0; i < this._slots.length - 1; i++) {
      const currentStop = this._slots[i].stop_minute;
      const nextStart = this._slots[i + 1].start_minute;
      if (nextStart <= currentStop) {
        this._setError(`Przedział ${i + 2} (start ${this._minuteToTime(nextStart)}) nakłada się na Przedział ${i + 1} (koniec ${this._minuteToTime(currentStop)}). Przedziały muszą być rozdzielone o co najmniej 1 minutę.`);
        this._render();
        return false;
      }
    }

    this._loading = true;
    this._error = null;
    this._render();

    try {
      const serviceData = {
        schedule_type: this._scheduleType,
        program_id: this._programId,
        slots: this._slots,
      };
      if (deviceId) {
        serviceData.device_id = deviceId;
      }

      await this._hass.callService("kospel", "set_program", serviceData);
      this._isSaved = true;
      this._hasUnsavedChanges = false;
      return true;
    } catch (err) {
      this._isSaved = false;
      this._setError(this._t("failed_save_program", { error: err.message || err }));
      return false;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _addSlot() {
    this._markUnsaved();
    if (this._slots.length >= 5) {
      this._setError(this._t("max_slots_error"));
      this._render();
      return;
    }

    if (this._slots.length === 0) {
      this._slots.push({ start_minute: 0, stop_minute: 1440, preset_id: 1 });
      this._activeSlotIndex = 0;
      this._render();
      return;
    }

    this._slots.sort((a, b) => a.start_minute - b.start_minute);
  }

  _addSlotInGap(gapStart, gapStop, clickedMin) {
    if (this._slots.length >= 5) {
      this._setError(this._t("max_slots_error"));
      this._render();
      return;
    }

    // Available gap duration in minutes (inclusive bounds [gapStart, gapStop])
    const maxDuration = gapStop - gapStart;
    if (maxDuration < 1) {
      return;
    }

    // Default duration is up to 120 minutes (or maxDuration if gap is smaller)
    const duration = Math.min(120, maxDuration);
    let newStart = gapStart;
    if (clickedMin !== undefined) {
      const halfDur = Math.floor(duration / 2);
      newStart = clickedMin - halfDur;
    }

    const maxStart = gapStop - duration;
    newStart = Math.max(gapStart, Math.min(maxStart, newStart));
    let newStop = newStart + duration;

    // Strict boundary safety
    if (newStop > gapStop) {
      newStop = gapStop;
    }
    if (newStart < gapStart) {
      newStart = gapStart;
    }

    this._markUnsaved();
    this._slots.push({
      start_minute: newStart,
      stop_minute: newStop,
      preset_id: 1,
    });

    this._slots.sort((a, b) => a.start_minute - b.start_minute);
    this._activeSlotIndex = this._slots.findIndex((s) => s.start_minute === newStart);
    this._render();
  }

  _addSlot() {
    if (this._slots.length >= 5) {
      this._setError(this._t("max_slots_error"));
      this._render();
      return;
    }

    this._slots.sort((a, b) => a.start_minute - b.start_minute);

    let bestGapStart = 0;
    let bestGapStop = 1439;
    let maxGapLength = 0;

    let prevStop = -1;
    for (let i = 0; i < this._slots.length; i++) {
      const gStart = prevStop < 0 ? 0 : prevStop + 1;
      const gStop = this._slots[i].start_minute - 1;
      const gapLength = gStop - gStart + 1;
      if (gapLength > maxGapLength) {
        maxGapLength = gapLength;
        bestGapStart = gStart;
        bestGapStop = gStop;
      }
      prevStop = this._slots[i].stop_minute;
    }

    const endGapStart = prevStop < 1440 ? prevStop + 1 : 1440;
    const endGapStop = 1439;
    const endGapLength = endGapStop - endGapStart + 1;
    if (endGapLength > maxGapLength) {
      maxGapLength = endGapLength;
      bestGapStart = endGapStart;
      bestGapStop = endGapStop;
    }

    if (maxGapLength < 1) {
      this._setError(this._t("max_slots_error"));
      this._render();
      return;
    }

    this._addSlotInGap(bestGapStart, bestGapStop, bestGapStart);
  }
  _removeSlot(index) {
    if (index < 0 || index >= this._slots.length) return;
    this._markUnsaved();
    this._slots.splice(index, 1);
    this._activeSlotIndex = Math.max(0, Math.min(index, this._slots.length - 1));
    this._render();
  }

  _render() {
    if (!this.shadowRoot) return;
    const presets = this._getPresets();

    const gapElements = [];
    let prevStop = -1;
    for (let i = 0; i < this._slots.length; i++) {
      const slot = this._slots[i];
      const gStart = prevStop < 0 ? 0 : prevStop + 1;
      const gStop = slot.start_minute - 1;
      if (gStop >= gStart) {
        gapElements.push({ start_minute: gStart, stop_minute: gStop });
      }
      prevStop = slot.stop_minute;
    }
    const endGStart = prevStop < 0 ? 0 : prevStop + 1;
    const endGStop = 1439;
    if (endGStop >= endGStart) {
      gapElements.push({ start_minute: endGStart, stop_minute: endGStop });
    }

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
          box-sizing: border-box;
          overflow: hidden;
          position: relative;
          isolation: isolate;
          contain: content;
          container-type: inline-size;
        }
        .controls-row {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          margin-bottom: 16px;
          width: 100%;
          box-sizing: border-box;
        }
        .control-group {
          flex: 1 1 130px;
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
          box-sizing: border-box;
        }
        .control-group label {
          font-size: 12px;
          color: var(--secondary-text-color, #727272);
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        select {
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--secondary-background-color, #f9f9f9);
          color: var(--primary-text-color, #212121);
          font-size: 14px;
          width: 100%;
          min-width: 0;
          box-sizing: border-box;
          text-overflow: ellipsis;
        }
        .input-time {
          padding: 6px 8px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--secondary-background-color, #f8fafc);
          color: var(--primary-text-color, #1e293b);
          font-size: 13px;
          font-weight: 600;
          font-family: inherit;
          cursor: pointer;
          transition: border-color 0.15s, box-shadow 0.15s;
          width: 90px;
          max-width: 100%;
          box-sizing: border-box;
          text-align: center;
        }
        .timeline-container {
          margin-bottom: 20px;
          user-select: none;
          touch-action: none;
        }
        .timeline-bar {
          position: relative;
          height: 36px;
          background: var(--secondary-background-color, #e0e0e0);
          border-radius: 8px;
          overflow: visible;
          display: flex;
        }
        .timeline-gap {
          position: absolute;
          height: 100%;
          top: 0;
          cursor: pointer;
          box-sizing: border-box;
          transition: background-color 0.2s, outline 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          background: transparent;
          z-index: 1;
        }
        .timeline-gap:hover {
          background: rgba(59, 130, 246, 0.18);
          outline: 2px dashed var(--primary-color, #3b82f6);
          outline-offset: -2px;
          border-radius: 6px;
          z-index: 5;
        }
        .gap-hover-hint {
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--primary-color, #3b82f6);
          opacity: 0;
          transition: opacity 0.15s, transform 0.15s;
          pointer-events: none;
        }
        .timeline-gap:hover .gap-hover-hint {
          opacity: 1;
          transform: scale(1.1);
        }
        .gap-hover-hint ha-icon {
          --mdc-icon-size: 20px;
          filter: drop-shadow(0 1px 2px rgba(255, 255, 255, 0.8));
        }
        .timeline-segment {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 11px;
          font-weight: 600;
          text-shadow: 0 1px 2px rgba(0,0,0,0.5);
          transition: background-color 0.2s;
          position: relative;
          box-sizing: border-box;
          border-right: 1px solid rgba(255,255,255,0.2);
          overflow: hidden;
        }
        .timeline-segment ha-icon {
          --mdc-icon-size: 18px;
          filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
          pointer-events: none;
        }
        .preset-group {
          display: flex;
          align-items: center;
          gap: 6px;
          flex: 1;
          min-width: 90px;
        }
        .preset-group ha-icon {
          --mdc-icon-size: 20px;
          flex-shrink: 0;
        }
        .timeline-handle {
          position: absolute;
          top: 2px;
          bottom: 2px;
          width: 8px;
          margin-left: -4px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.4);
          border-radius: 4px;
          cursor: ew-resize;
          z-index: 2;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
          touch-action: none;
          transition: background-color 0.15s, border-color 0.15s, transform 0.15s;
        }
        .timeline-handle:hover, .timeline-handle.dragging {
          background: var(--primary-color, #3b82f6);
          border-color: #2563eb;
          transform: scale(1.15);
          z-index: 3;
        }
        .drag-tooltip {
          position: absolute;
          top: -32px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(15, 23, 42, 0.9);
          color: #fff;
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
          white-space: nowrap;
          pointer-events: none;
          display: none;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .timeline-handle:hover .drag-tooltip,
        .timeline-handle.dragging .drag-tooltip {
          display: block;
        }
        .timeline-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 6px;
          font-size: 11px;
          color: var(--secondary-text-color, #727272);
          font-weight: 500;
        }
        .section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .section-title {
          font-size: 14px;
          font-weight: 700;
          color: var(--primary-text-color, #1e293b);
        }
        .btn-add-slot {
          font-size: 12px;
          padding: 4px 10px;
          background: var(--secondary-background-color, #f1f5f9);
          color: var(--primary-text-color, #334155);
          border: 1px solid var(--divider-color, #cbd5e1);
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
        .btn-add-slot:hover {
          background: var(--primary-color, #3b82f6);
          color: #fff;
          border-color: var(--primary-color, #3b82f6);
        }
        .slots-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-bottom: 16px;
        }
        .slot-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          border-radius: 8px;
          background: var(--secondary-background-color, #f9f9f9);
          border: 1px solid var(--divider-color, #e5e7eb);
          flex-wrap: wrap;
          box-sizing: border-box;
          width: 100%;
        }
        .slot-item.active {
          border-color: var(--primary-color, #3b82f6);
        }
        .slot-time {
          display: flex;
          align-items: center;
          gap: 4px;
          flex-shrink: 0;
        }
        .select-preset {
          flex: 1;
          min-width: 90px;
          text-overflow: ellipsis;
        }
        .btn-danger {
          background: #ef4444;
          color: #fff;
          padding: 6px 12px;
          font-size: 12px;
          border-radius: 6px;
          flex-shrink: 0;
        }
        .btn-remove {
          background: transparent !important;
          border: none !important;
          color: #ef4444 !important;
          padding: 0;
          width: 28px;
          height: 28px;
          border-radius: 0;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          margin-left: auto;
          flex-shrink: 0;
          cursor: pointer;
          box-shadow: none !important;
          outline: none !important;
        }
        .btn-remove:hover {
          background: transparent !important;
          color: #dc2626 !important;
          opacity: 0.8;
        }
        .btn-remove ha-icon {
          --mdc-icon-size: 22px;
          color: #ef4444;
        }
        @container (max-width: 360px), @media (max-width: 480px) {
          .controls-row {
            flex-direction: column;
            gap: 8px;
          }
          .slot-item {
            flex-direction: column;
            align-items: stretch;
            gap: 8px;
          }
          .slot-time {
            justify-content: space-between;
            width: 100%;
          }
          .input-time {
            flex: 1;
            width: auto;
            max-width: 130px;
          }
          .select-preset {
            width: 100%;
          }
          .btn-remove {
            width: 100%;
            justify-content: center;
            margin-left: 0;
          }
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
        .empty-state-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 28px 16px;
          border: 2px dashed var(--divider-color, #cbd5e1);
          border-radius: 12px;
          background: var(--secondary-background-color, #f8fafc);
          text-align: center;
          margin-bottom: 16px;
        }
        .empty-icon {
          --mdc-icon-size: 44px;
          color: var(--secondary-text-color, #94a3b8);
          margin-bottom: 10px;
        }
        .empty-title {
          font-size: 15px;
          font-weight: 700;
          color: var(--primary-text-color, #1e293b);
          margin-bottom: 4px;
        }
        .empty-subtitle {
          font-size: 13px;
          color: var(--secondary-text-color, #64748b);
          margin-bottom: 14px;
          max-width: 300px;
          line-height: 1.4;
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

        <div class="controls-row">
          <div class="control-group">
            <label>${this._t("schedule_type")}</label>
            <select id="select-type">
              <option value="ch" ${this._scheduleType === "ch" ? "selected" : ""}>${this._t("ch")}</option>
              <option value="dhw" ${this._scheduleType === "dhw" ? "selected" : ""}>${this._t("dhw")}</option>
              <option value="circulation" ${this._scheduleType === "circulation" ? "selected" : ""}>${this._t("circulation")}</option>
            </select>
          </div>

          <div class="control-group">
            <label>${this._t("program_number")}</label>
            <select id="select-program">
              ${[1, 2, 3, 4, 5, 6, 7, 8]
                .map((p) => `<option value="${p}" ${this._programId === p ? "selected" : ""}>${this._t("program_n", { n: p })}</option>`)
                .join("")}
            </select>
          </div>
        </div>

        <div class="timeline-container">
          <div class="timeline-bar" id="timeline-bar">
            ${this._slots.length === 0
                ? `<div class="timeline-gap empty-timeline-gap" 
                        style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;"
                        title="${this._t("click_to_add_slot")}">
                     <div class="gap-hover-hint" style="opacity: 1;">
                       <ha-icon icon="mdi:plus-circle-outline"></ha-icon>
                       <span>${this._t("empty_program_timeline")}</span>
                     </div>
                   </div>`
                : `
                  ${gapElements
                    .map((gap) => {
                      const leftPct = ((gap.start_minute / 1440) * 100).toFixed(2);
                      const gapDur = gap.stop_minute - gap.start_minute + 1;
                      const widthPct = ((gapDur / 1440) * 100).toFixed(2);
                      return `
                        <div class="timeline-gap"
                             style="position: absolute; left: ${leftPct}%; width: ${widthPct}%;"
                             data-gap-start="${gap.start_minute}"
                             data-gap-stop="${gap.stop_minute}"
                             title="${this._t("click_to_add_slot")}">
                          <div class="gap-hover-hint">
                            <ha-icon icon="mdi:plus"></ha-icon>
                          </div>
                        </div>
                      `;
                    })
                    .join("")}

                  ${this._slots
                    .map((slot, idx) => {
                      const duration = slot.stop_minute - slot.start_minute;
                      const leftPct = ((slot.start_minute / 1440) * 100).toFixed(2);
                      const widthPct = ((duration / 1440) * 100).toFixed(2);
                      const info = this._getPresetInfo(slot.preset_id);
                      return `
                        <div class="timeline-segment" 
                             style="position: absolute; left: ${leftPct}%; width: ${widthPct}%; background-color: ${info.color};"
                             title="${info.name}: ${this._minuteToDisplayTime(slot.start_minute)} - ${this._minuteToDisplayTime(slot.stop_minute)}"
                             data-idx="${idx}">
                          ${duration >= 30 ? `<ha-icon icon="${info.icon}"></ha-icon>` : ""}
                        </div>
                      `;
                    })
                    .join("")}

                  ${this._slots
                    .map((slot, idx) => {
                      const startPct = ((slot.start_minute / 1440) * 100).toFixed(2);
                      const stopPct = ((slot.stop_minute / 1440) * 100).toFixed(2);
                      return `
                        <!-- Start Handle for Slot ${idx} -->
                        <div class="timeline-handle" 
                             style="left: ${startPct}%;" 
                             data-handle-type="slot-start"
                             data-handle-idx="${idx}"
                             title="${this._t("drag_start_time", { time: this._minuteToDisplayTime(slot.start_minute) })}">
                          <div class="drag-tooltip">${this._minuteToDisplayTime(slot.start_minute)}</div>
                        </div>

                        <!-- Stop Handle for Slot ${idx} -->
                        <div class="timeline-handle" 
                             style="left: ${stopPct}%;" 
                             data-handle-type="slot-stop"
                             data-handle-idx="${idx}"
                             title="${this._t("drag_end_time", { time: this._minuteToDisplayTime(slot.stop_minute) })}">
                          <div class="drag-tooltip">${this._minuteToDisplayTime(slot.stop_minute)}</div>
                        </div>
                      `;
                    })
                    .join("")}
                `
            }
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
          ${this._slots.length === 0
              ? `
                <div class="empty-state-card">
                  <ha-icon icon="mdi:calendar-clock" class="empty-icon"></ha-icon>
                  <div class="empty-title">${this._t("empty_program_title", { n: this._programId })}</div>
                  <div class="empty-subtitle">${this._t("empty_program_info")}</div>
                  <button type="button" class="btn-primary" id="btn-add-slot-empty">
                    <ha-icon icon="mdi:plus"></ha-icon> ${this._t("add_slot")}
                  </button>
                </div>
              `
              : `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <strong style="font-size: 14px;">${this._t("time_slots", { current: this._slots.length, max: 5 })}</strong>
                  <button type="button" class="btn-secondary" id="btn-add-slot" style="padding: 6px 12px; font-size: 12px;">
                    ${this._t("add_slot")}
                  </button>
                </div>

                ${this._slots
                  .map((slot, idx) => {
                    const info = this._getPresetInfo(slot.preset_id);
                    const minStart = idx > 0 ? this._slots[idx - 1].stop_minute : 0;
                    const maxStart = slot.stop_minute - 1;
                    const minStop = slot.start_minute + 1;
                    const maxStop = idx < this._slots.length - 1 ? this._slots[idx + 1].start_minute : 1440;
                    return `
                      <div class="slot-item ${idx === this._activeSlotIndex ? "active" : ""}">
                        <div class="slot-time">
                          <input type="time" class="input-time input-start" data-idx="${idx}" 
                                 min="${this._minuteToTime(minStart)}"
                                 max="${this._minuteToTime(maxStart)}"
                                 value="${this._minuteToTime(slot.start_minute)}">
                          <span>${this._t("to")}</span>
                          <input type="time" class="input-time input-stop" data-idx="${idx}"
                                 min="${this._minuteToTime(minStop)}"
                                 max="${this._minuteToTime(maxStop)}"
                                 value="${this._minuteToTime(slot.stop_minute)}">
                        </div>

                        <div class="preset-group">
                          <ha-icon icon="${info.icon}" style="color: ${info.color};"></ha-icon>
                          <select class="select-preset" data-idx="${idx}" style="flex: 1;">
                            ${presets
                              .map(
                                (p) =>
                                  `<option value="${p.id}" ${slot.preset_id === p.id ? "selected" : ""}>${p.name}</option>`
                              )
                              .join("")}
                          </select>
                        </div>

                        <button type="button" class="btn-remove" data-idx="${idx}" title="${this._t("remove")}"><ha-icon icon="mdi:close"></ha-icon></button>
                      </div>
                    `;
                  })
                  .join("")}
              `
          }
        </div>

        <div class="btn-row">
          <button type="button" class="${this._hasUnsavedChanges ? "btn-danger" : "btn-secondary"}" id="btn-cancel" ${!this._hasUnsavedChanges || this._loading ? "disabled" : ""}>
            ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:close"></ha-icon>'} ${this._t("cancel")}
          </button>

          ${
            this._hasUnsavedChanges
              ? `<button type="button" class="btn-success" id="btn-save" ${this._loading ? "disabled" : ""}>
                   ${this._loading ? '<div class="spinner"></div>' : '<ha-icon icon="mdi:content-save"></ha-icon>'} ${this._t("save_program")}
                 </button>`
              : `<button type="button" class="btn-primary" id="btn-save" ${this._loading ? "disabled" : ""}>
                   <ha-icon icon="mdi:check"></ha-icon> ${this._t("program_saved")}
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
              ${this._t("unsaved_body_program", { program: this._pendingSwitch ? this._pendingSwitch.newProgramId : this._programId, type: this._t(this._pendingSwitch ? this._pendingSwitch.newType : this._scheduleType) })}
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
          this._pendingSwitch = { newType, newProgramId: this._programId };
          this._confirmModalOpen = true;
          this._render();
        } else {
          this._performSwitch(newType, this._programId);
        }
      });
    }

    // Program select with unsaved changes prompt & auto-fetch
    const selectProgram = root.querySelector("#select-program");
    if (selectProgram) {
      selectProgram.addEventListener("change", (e) => {
        const newProgId = parseInt(e.target.value, 10);
        if (newProgId === this._programId) return;

        if (this._hasUnsavedChanges) {
          selectProgram.value = this._programId;
          this._pendingSwitch = { newType: this._scheduleType, newProgramId: newProgId };
          this._confirmModalOpen = true;
          this._render();
        } else {
          this._performSwitch(this._scheduleType, newProgId);
        }
      });
    }

    // Unsaved changes modal button handlers
    if (this._confirmModalOpen) {
      const btnModalSave = root.querySelector("#btn-modal-save");
      if (btnModalSave) {
        btnModalSave.addEventListener("click", async () => {
          this._confirmModalOpen = false;
          const success = await this._saveProgram();
          if (success !== false && this._pendingSwitch) {
            await this._performSwitch(this._pendingSwitch.newType, this._pendingSwitch.newProgramId);
          }
        });
      }

      const btnModalAbandon = root.querySelector("#btn-modal-abandon");
      if (btnModalAbandon) {
        btnModalAbandon.addEventListener("click", async () => {
          this._confirmModalOpen = false;
          if (this._pendingSwitch) {
            await this._performSwitch(this._pendingSwitch.newType, this._pendingSwitch.newProgramId);
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
          this._loadProgram();
        }
      });
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

    const btnAddEmpty = root.querySelector("#btn-add-slot-empty");
    if (btnAddEmpty) {
      btnAddEmpty.addEventListener("click", () => this._addSlot());
    }

    // Timeline boundary drag handles
    const timelineBar = root.querySelector("#timeline-bar");
    if (timelineBar) {
      root.querySelectorAll(".timeline-handle").forEach((handle) => {
        handle.addEventListener("pointerdown", (e) => {
          e.preventDefault();
          const handleType = handle.dataset.handleType;
          const handleIdx = parseInt(handle.dataset.handleIdx, 10);
          this._isDragging = true;
          handle.classList.add("dragging");
          const tooltip = handle.querySelector(".drag-tooltip");

          try {
            handle.setPointerCapture(e.pointerId);
          } catch (err) {}

          const onPointerMove = (moveEv) => {
            const rect = timelineBar.getBoundingClientRect();
            if (!rect.width) return;
            const x = moveEv.clientX - rect.left;
            const pct = Math.max(0, Math.min(1, x / rect.width));
            const rawMin = Math.round(pct * 1440);

            // Snap to configured sliding precision (1-60 minutes, default 5)
            const precision = this._slidingPrecision || 5;
            const snappedMin = Math.round(rawMin / precision) * precision;
            const minDuration = Math.min(5, precision);

            if (handleType === "slot-start") {
              const minBound = handleIdx > 0 ? this._slots[handleIdx - 1].stop_minute + 1 : 0;
              const maxBound = this._slots[handleIdx].stop_minute - minDuration;
              const clampedMin = Math.max(minBound, Math.min(maxBound, snappedMin));

              if (this._slots[handleIdx].start_minute !== clampedMin) {
                this._slots[handleIdx].start_minute = clampedMin;
                this._markUnsaved();

                const posPct = ((clampedMin / 1440) * 100).toFixed(2);
                handle.style.left = `${posPct}%`;
                if (tooltip) tooltip.textContent = this._minuteToDisplayTime(clampedMin);

                const seg = root.querySelector(`.timeline-segment[data-idx="${handleIdx}"]`);
                if (seg) {
                  const dur = this._slots[handleIdx].stop_minute - clampedMin;
                  seg.style.left = `${posPct}%`;
                  seg.style.width = `${((dur / 1440) * 100).toFixed(2)}%`;
                }

                const startInput = root.querySelector(`.input-start[data-idx="${handleIdx}"]`);
                if (startInput) startInput.value = this._minuteToTime(clampedMin);
              }
            } else if (handleType === "slot-stop") {
              const minBound = this._slots[handleIdx].start_minute + minDuration;
              const maxBound = handleIdx < this._slots.length - 1 ? this._slots[handleIdx + 1].start_minute - 1 : 1440;
              const clampedMin = Math.max(minBound, Math.min(maxBound, snappedMin));

              if (this._slots[handleIdx].stop_minute !== clampedMin) {
                this._slots[handleIdx].stop_minute = clampedMin;
                this._markUnsaved();

                const posPct = ((clampedMin / 1440) * 100).toFixed(2);
                handle.style.left = `${posPct}%`;
                if (tooltip) tooltip.textContent = this._minuteToDisplayTime(clampedMin);

                const seg = root.querySelector(`.timeline-segment[data-idx="${handleIdx}"]`);
                if (seg) {
                  const startPct = ((this._slots[handleIdx].start_minute / 1440) * 100).toFixed(2);
                  const dur = clampedMin - this._slots[handleIdx].start_minute;
                  seg.style.left = `${startPct}%`;
                  seg.style.width = `${((dur / 1440) * 100).toFixed(2)}%`;
                }

                const stopInput = root.querySelector(`.input-stop[data-idx="${handleIdx}"]`);
                if (stopInput) stopInput.value = this._minuteToTime(clampedMin);
              }
            }
          };

          const onPointerUp = (upEv) => {
            handle.classList.remove("dragging");
            try {
              handle.releasePointerCapture(upEv.pointerId);
            } catch (err) {}
            window.removeEventListener("pointermove", onPointerMove);
            window.removeEventListener("pointerup", onPointerUp);
            window.removeEventListener("pointercancel", onPointerUp);
            setTimeout(() => {
              this._isDragging = false;
            }, 50);
            this._render();
          };

          window.addEventListener("pointermove", onPointerMove);
          window.addEventListener("pointerup", onPointerUp);
          window.addEventListener("pointercancel", onPointerUp);
        });
      });
    }

    // Click empty gap on timeline bar to add a new slot right at clicked position
    root.querySelectorAll(".timeline-gap").forEach((gapEl) => {
      gapEl.addEventListener("click", (e) => {
        if (this._isDragging) return;

        const gapStartAttr = gapEl.dataset.gapStart;
        const gapStopAttr = gapEl.dataset.gapStop;
        if (gapStartAttr === undefined || gapStopAttr === undefined) {
          // Empty program timeline
          this._addSlotInGap(0, 1439, 0);
          return;
        }

        const gapStart = parseInt(gapStartAttr, 10);
        const gapStop = parseInt(gapStopAttr, 10);

        const rect = gapEl.getBoundingClientRect();
        let clickedMin = gapStart;
        if (rect.width > 0) {
          const clickX = e.clientX - rect.left;
          const gapDuration = gapStop - gapStart;
          const offsetMin = Math.round((clickX / rect.width) * gapDuration);
          clickedMin = gapStart + offsetMin;
        }

        this._addSlotInGap(gapStart, gapStop, clickedMin);
      });
    });

    // Remove slot buttons
    root.querySelectorAll(".btn-remove").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.currentTarget.dataset.idx, 10);
        this._removeSlot(idx);
      });
    });

    // Invoke native out-of-the-box OS/browser time picker dialog on tap/click
    root.querySelectorAll(".input-time").forEach((input) => {
      input.addEventListener("click", (e) => {
        if (typeof e.target.showPicker === "function") {
          try {
            e.target.showPicker();
          } catch (err) {}
        }
      });
    });

    // Time input changes with boundary clamping
    root.querySelectorAll(".input-start").forEach((input) => {
      input.addEventListener("change", (e) => {
        this._markUnsaved();
        const idx = parseInt(e.target.dataset.idx, 10);
        const minAllowed = idx > 0 ? this._slots[idx - 1].stop_minute : 0;
        const maxAllowed = this._slots[idx].stop_minute - 1;
        const rawMin = this._timeToMinute(e.target.value);
        const clampedMin = Math.max(minAllowed, Math.min(maxAllowed, rawMin));

        this._slots[idx].start_minute = clampedMin;
        this._render();
      });
    });

    root.querySelectorAll(".input-stop").forEach((input) => {
      input.addEventListener("change", (e) => {
        this._markUnsaved();
        const idx = parseInt(e.target.dataset.idx, 10);
        const minAllowed = this._slots[idx].start_minute + 1;
        const maxAllowed = idx < this._slots.length - 1 ? this._slots[idx + 1].start_minute : 1440;
        const rawMin = this._timeToMinute(e.target.value);
        const clampedMin = Math.max(minAllowed, Math.min(maxAllowed, rawMin));

        this._slots[idx].stop_minute = clampedMin;
        this._render();
      });
    });

    // Preset select changes
    root.querySelectorAll(".select-preset").forEach((select) => {
      select.addEventListener("change", (e) => {
        this._markUnsaved();
        const idx = parseInt(e.target.dataset.idx, 10);
        this._slots[idx].preset_id = parseInt(e.target.value, 10);
        this._render();
      });
    });
  }
}

class KospelProgramCardEditor extends HTMLElement {
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
      { name: "sliding_precision", selector: { number: { min: 1, max: 60, step: 1, mode: "box" } } },
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
      sliding_precision: 5,
      ...this._config,
    };
    this._haForm.schema = schema;
    this._haForm.computeLabel = (schema) => {
      if (schema.name === "device_id") return "Kospel Device";
      if (schema.name === "sliding_precision") return "Sliding Precision (minutes, 1-60)";
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

if (!customElements.get("kospel-program-card")) {
  customElements.define("kospel-program-card", KospelProgramCard);
}
if (!customElements.get("kospel-program-card-editor")) {
  customElements.define("kospel-program-card-editor", KospelProgramCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "kospel-program-card")) {
  window.customCards.push({
    type: "kospel-program-card",
    name: "Kospel Daily Program Card",
    description: "View and edit Kospel heating daily time slots and presets",
  });
}

function forceLovelaceRebuild() {
  window.dispatchEvent(new CustomEvent("ll-rebuild"));
  window.dispatchEvent(new Event("location-changed"));

  try {
    const ha = document.querySelector("home-assistant");
    if (!ha || !ha.shadowRoot) return;
    const main = ha.shadowRoot.querySelector("home-assistant-main");
    if (!main || !main.shadowRoot) return;
    const drawer = main.shadowRoot.querySelector("ha-drawer");
    if (!drawer) return;
    const resolver = drawer.querySelector("partial-panel-resolver");
    if (!resolver) return;
    const panel = resolver.querySelector("ha-panel-lovelace");
    if (!panel || !panel.shadowRoot) return;
    const root = panel.shadowRoot.querySelector("hui-root");
    if (!root || !root.shadowRoot) return;

    const errorCards = root.shadowRoot.querySelectorAll("hui-error-card, hui-card-element-editor");
    errorCards.forEach((card) => {
      if (card.textContent && card.textContent.includes("kospel-program-card")) {
        const parent = card.parentElement;
        const config = card._config;
        if (parent && config) {
          const newCard = document.createElement("kospel-program-card");
          if (typeof newCard.setConfig === "function") {
            newCard.setConfig(config);
            if (card.hass) newCard.hass = card.hass;
            parent.replaceChild(newCard, card);
          }
        }
      }
    });
  } catch (err) {}
}

forceLovelaceRebuild();
setTimeout(forceLovelaceRebuild, 50);
setTimeout(forceLovelaceRebuild, 250);
setTimeout(forceLovelaceRebuild, 1000);
