# Kospel Frontend Cards & Development Guide

This document describes the custom Lovelace cards integrated into `ha-kospel-cmi`, their architecture, design system, and frontend development conventions.

---

## 1. Overview of Custom Cards

The integration includes two custom Lovelace dashboard cards that are automatically registered in Home Assistant:

### 1. `kospel-program-card` (Daily Program Editor)
* **Purpose**: Allows users to configure and edit up to 8 Daily Programs for Central Heating (CH), Domestic Hot Water (DHW), and Circulation schedules.
* **Features**:
  * **24-Hour Timeline Bar**: Color-coded visualization showing time slots and mode icons (`mdi:thermometer`, `mdi:snowflake`, `mdi:leaf`, etc.).
  * **Interactive Drag-and-Drop Handles**: Move slot boundaries directly on the timeline bar with touch and mouse pointer support.
  * **Strict 1-Minute Separation**: Ensures slot stop times do not overlap or collide with subsequent slot start times (`next_start > current_stop`).
  * **Smart Slot Addition**: Clicking `+ Dodaj przedział` automatically locates the largest available empty gap in the 24-hour day and inserts the new slot there.
  * **Unsaved Changes Prompt**: Warns users with a confirm modal if they attempt to switch programs or schedule types before saving.
  * **Native Device Selector**: Integrated `KospelProgramCardEditor` form with native Home Assistant device picker (`selector: { device: { filter: { integration: "kospel" } } }`).

### 2. `kospel-weekday-card` (Weekday Schedule Dashboard)
* **Purpose**: Assigns Daily Programs (1–8) to each day of the week (Monday through Sunday).
* **Features**:
  * **Read-Only Daily Visualization**: Displays compact 24-hour timeline bars for each day of the week, showing assigned schedule profiles at a glance.
  * **Smart Boundary Edge Labels**: Displays exact slot edge timestamps (`00:00`, `24:00`, and slot `start`/`stop` times) under each daily bar.
  * **Anti-Collision Filtering**: Automatically filters out colliding intermediate timestamps (minimum 120-minute spacing), keeping timestamps clean and legible.
  * **Unsaved Changes Prompt**: Prevents accidental data loss when switching schedule types.
  * **Native Device Selector**: Integrated `KospelWeekdayCardEditor` form with device picker.

---

## 2. Architecture & Asset Serving

### Dynamic Endpoint & Resource Registration
1. **HTTP View Endpoint**: `custom_components/kospel/frontend/__init__.py` registers a static HTTP view serving files from `custom_components/kospel/frontend/` under `/kospel_static/`.
2. **Automatic Lovelace Resource Binding**: On integration setup, `async_register_frontend_cards()` automatically registers `/kospel_static/kospel-program-card.js` and `/kospel_static/kospel-weekday-card.js` as extra module URLs in Home Assistant frontend resources. Users do **not** need to manually configure YAML resource links.
3. **Card Picker Integration**: Both cards register themselves in `window.customCards`:
   ```javascript
   window.customCards = window.customCards || [];
   if (!window.customCards.some((c) => c.type === "kospel-program-card")) {
     window.customCards.push({
       type: "kospel-program-card",
       name: "Kospel Daily Program Card",
       description: "Interactive timeline editor for Kospel Daily Programs 1-8",
     });
   }
   ```

---

## 3. Style Guide & Design Conventions

### Framework-Free Web Components
* Cards are built as native Custom Elements extending `HTMLElement`, using Shadow DOM (`this.attachShadow({ mode: "open" })`).
* No build tools, transpilers, or node dependencies are required. All frontend code is pure vanilla JavaScript (ES6+ Modules).

### Theme Tokens & CSS Variables
All styling utilizes Home Assistant CSS tokens so components adapt seamlessly to light, dark, and custom themes:

| Token | Usage |
| :--- | :--- |
| `var(--primary-text-color)` | Card titles, slot times, select labels |
| `var(--secondary-text-color)` | Subtitles, labels, empty state text |
| `var(--card-background-color)` | Main card background, modal background |
| `var(--secondary-background-color)` | Timeline background, day row card background |
| `var(--ha-card-border-radius)` | Outer card border radius (default `12px`) |
| `var(--divider-color)` | Borders and dividers |

### Temperature Preset Color Hierarchy & Icons
Temperature modes use Home Assistant's native `<ha-icon icon="mdi:...">` component with a unified icon family and high-contrast color palette:

| Preset Mode | Icon | Hex Color | Visual Description |
| :--- | :--- | :--- | :--- |
| **Ochrona przed zamarzaniem** | `mdi:snowflake` | `#3b82f6` | Royal Blue |
| **Ekonomiczny (Eco)** | `mdi:leaf` | `#10b981` | Emerald Green |
| **Komfort-** | `mdi:thermometer-minus` | `#facc15` | Bright Golden Sun Yellow |
| **Komfort** | `mdi:thermometer` | `#f97316` | Warm Orange |
| **Komfort+** | `mdi:thermometer-plus` | `#ef4444` | Vibrant Red |
| **Wyłączone (Off)** | `mdi:power` | `#6b7280` | Neutral Slate Grey |
| **Włączone (On)** | `mdi:sync` | `#3b82f6` | Royal Blue |

### Slot Removal Button Styling
Remove slot buttons (`.btn-remove`) are designed to be subtle and non-intrusive:
```css
.btn-remove {
  background: transparent !important;
  border: none !important;
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
}
```

### Save Status Label
To keep status labels clean and concise, success state buttons display:
* Polish: `"Zapisano"`
* English: `"Saved"`

---

## 4. Interaction & Event Conventions

### Touch & Pointer Events
Drag handles on the timeline bar use the HTML5 Pointer Events API for unified mouse and touch gesture handling:
* `pointerdown`: Invokes `e.preventDefault()`, adds `dragging` class, and captures pointer via `handle.setPointerCapture(e.pointerId)`.
* `pointermove`: Calculates relative X percentage against `timelineBar.getBoundingClientRect()`, snaps to precision interval (`5 min`), and applies boundary clamping.
* `pointerup` / `pointercancel`: Releases pointer capture and re-renders card state.

### Boundary Clamping Rules
To guarantee schedule validity and prevent overlapping time slots:
* **Slot Start Handle**: Clamped between `(prev_slot.stop_minute + 1)` and `(current_slot.stop_minute - 1)`.
* **Slot Stop Handle**: Clamped between `(current_slot.start_minute + 1)` and `(next_slot.start_minute - 1)`.

### Anti-Collision Label Algorithm
For read-only weekday cards (`kospel-weekday-card`), boundary edge labels under the timeline bar apply a minimum gap threshold (`MIN_GAP_MINUTES = 120`) to prevent text collisions:
1. Always include `00:00` (aligned left) and `24:00` (aligned right).
2. Deduplicate exact matching timestamps (e.g. continuous slot boundaries).
3. If an intermediate timestamp is closer than 120 minutes to the previously rendered label or the end label, skip it to prevent overlapping text.

---

## 5. Internationalization (i18n)

Cards include a built-in `TRANSLATIONS` dictionary supporting Polish (`pl`) and English (`en`):
```javascript
function localize(key, lang = "en", placeholders = {}) {
  const langKey = (lang || "en").toLowerCase().split("-")[0];
  const dict = TRANSLATIONS[langKey] || TRANSLATIONS.en;
  let text = dict[key] || TRANSLATIONS.en[key] || key;
  for (const [pKey, pVal] of Object.entries(placeholders)) {
    text = text.replace(new RegExp(`\\{${pKey}\\}`, "g"), pVal);
  }
  return text;
}
```
Language is detected automatically from Home Assistant's active user locale (`hass.language`).
