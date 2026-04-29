# Documentation: Weather Now

## Project Overview
**Weather Now** is a dual-platform weather reporting solution designed for high-contrast, minimalist displays. It originated as a custom firmware implementation for **TRMNL** (e-ink hardware) and was subsequently adapted into a **Standalone JavaScript** application for macOS desktop widgets (via Plash) and legacy E-Ink browsers (Amazon Kindle).

The system interfaces with the **Open-Meteo API** to provide localized, context-aware weather summaries that prioritize future trends over redundant current data.

---

## 1. Implementation Path A: TRMNL (Liquid)

The TRMNL version is designed to run on the TRMNL hardware backend using the Liquid templating language. Since TRMNL is a server-side environment, the logic handles time offsets and daylight savings manually.

### A. Environment Configuration
* **Language:** Liquid
* **Data Source:** Custom API Integration (Open-Meteo)
* **Coordinates:** `latitude=56.60712432274488`, `longitude=-3.0858753489219812`
* **Timezone Logic:** Uses a manual BST/GMT offset block to adjust `hr_now` based on the last Sunday of March and October.

### B. Deployment
1.  Create a **New Private Plugin** in the TRMNL Dashboard.
2.  Set the **Data Source** to the Open-Meteo URL.
3.  Paste the Liquid code into the **Markup** section.
4.  Ensure no `{% comment %}` tags remain, as some Liquid parsers on the backend may trigger syntax errors if tags are left unclosed.

---

## 2. Implementation Path B: Standalone (JavaScript)

The Standalone version is a self-contained `.html` file that performs its own API fetches. It is optimized for macOS desktop use and the Kindle Paperwhite "Experimental Browser."

### A. Technical Architecture
* **Languages:** HTML5, CSS3, Vanilla JS (ES6+).
* **Timezone Handling:** Managed via the `&timezone=Europe/London` API parameter. 
* **Unit Control:** Explicitly requests `&wind_speed_unit=mph` to ensure consistency across platforms.

### B. Deployment
* **macOS Widget:** Save as `weather.html` and load into **Plash**. Set the refresh interval to 15–30 minutes.
* **Kindle:** Host the file on a local/public URL. The CSS includes a `rotate(-90deg)` media query to force landscape orientation on portrait-locked Kindle browsers.

---

## 3. Core Features & "Secret Sauce" Logic

Both versions of **Weather Now** share the same logical "blindfold" architecture to ensure the dashboard remains informative throughout the day.

### A. The "Blindfold" Methodology
To prevent repeating data shown in the 5-hour hourly scale, the **Later** and **Overnight** sections ignore the immediate future. All secondary scans begin strictly at `hr_now + 6`.

### B. "Later" Section Logic
* **High Temperature:** Compares the max temperature from `hr_now + 6` through Midnight against the official daily high. If the daily high has already occurred (or is currently visible in the hourly scale), the High display is hidden.
* **Low Temperature:** Scans from the end of the hourly scale through to 6:00 AM the following morning.
* **Sync Logic:** The `scanEnd` is set to `endOfDayIdx + 7` to ensure the "Later" low matches the "Overnight" low exactly.

### C. The "Overnight" Summary
* **Fixed Window:** Targets 10:00 PM to 6:00 AM.
* **Precipitation Risk:** Identifies the specific hour of highest risk and outputs the time (e.g., "Rain at 4am").
* **Condition Mapping:** Translates WMO codes (0-99) into human-readable strings, adjusted for night-time visibility (e.g., Code 0 = "Clear").

---

## 4. Visual Style & Formatting

| Feature | Specification |
| :--- | :--- |
| **Canvas Size** | 840px x 480px |
| **Typography** | `Georgia, serif` (Main), `Sans-Serif` (System) |
| **Primary Temp** | 115px (Line-height 0.8) |
| **Grid Layout** | 5-column CSS Grid with a terminal "Later" column |
| **Flourish** | Custom SVG "Swoosh" path for editorial aesthetic |

---

## 5. Maintenance & Troubleshooting

* **Coordinates:** Always use high-precision decimals (`56.607...`) to ensure the Open-Meteo 1km grid model matches across all devices.
* **Wind Discrepancies:** The Open-Meteo API defaults to km/h. Standalone implementations must include the `wind_speed_unit=mph` flag in the URL.
* **Liquid Errors:** If the TRMNL version fails to render, check for unclosed Liquid tags or improper array indexing. **Weather Now** uses `index.of` logic in JS but requires direct index targeting in Liquid.
* **Kindle Scaling:** If the dashboard clips on a Kindle, adjust the `scale(0.92)` factor in the CSS `kindle-wrapper` to compensate for specific device bezel/viewport differences.
