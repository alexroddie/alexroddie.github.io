# Documentation: Weather Now

## Project Overview
**Weather Now** is a standalone, browser-based software solution designed for high-legibility displays, macOS desktop widgets, and E-Ink devices (specifically the Amazon Kindle Paperwhite). 

The software interfaces with the **Open-Meteo API** to provide a localized, forward-looking weather summary. Its primary design philosophy is **contextual awareness**: showing not just current conditions, but future trends relative to the weather the user has already seen.

---

## 1. Technical Architecture

**Weather Now** is built as a single-file application using standard web technologies. This architecture ensures portability and ease of deployment without the need for a server-side backend.

* **Core Languages:** HTML5, CSS3, and Vanilla JavaScript (ES6+).
* **Data Provider:** [Open-Meteo API](https://open-meteo.com/).
* **Timezone Handling:** Managed via the `Europe/London` parameter. The JavaScript engine utilizes `Intl.DateTimeFormat` to handle BST/GMT transitions automatically.
* **Coordinate System:** Precision geolocating based on user-defined high-resolution latitude and longitude.

---

## 2. Core Logic & Features

### A. The "Blindfold" Methodology
To prevent information redundancy, **Weather Now** utilizes "blindfold" logic for its summary sections. While the hourly scale shows the immediate 5-hour window, the **"Later"** and **"Overnight"** sections ignore those hours. The scan for future trends begins strictly at `hr_now + 6`.

### B. "Later" Section Logic
This section is designed to answer: *"Is the day's peak over, and how cold will it get tonight?"*
* **High Temperature:** Compares the maximum temperature found in the evening (`hr_now + 6` to Midnight) against the official daily high. If the daily high has already passed, the display hides the high temperature to reduce visual clutter.
* **Low Temperature:** Scans from the end of the hourly scale through to 6:00 AM the following morning to capture the true upcoming minimum.

### C. The "Overnight" Summary
This section specifically targets the sleeping hours (10:00 PM to 6:00 AM).
* Calculates the absolute low during this window.
* Identifies the specific hour of highest precipitation risk.
* Maps WMO codes to human-readable strings (e.g., "Mostly clear").

### D. Unit & Condition Mapping
* **Wind Units:** All wind speeds and gusts are requested in **mph**.
* **WMO Translation:** The software translates World Meteorological Organization (WMO) codes into descriptors, adjusted by `isNight` logic (e.g., Code `0` displays as "Sunny" during the day and "Clear" at night).

---

## 3. Visual Formatting

The UI is optimized for **high-contrast reading** and editorial aesthetics.

| Element | Specification |
| :--- | :--- |
| **Typography** | `Georgia, serif` for a classic, newspaper feel. |
| **Main Temp** | `115px`, line-height `.8` for visual hierarchy. |
| **Hourly Row** | 5-column CSS Grid with a terminal "Later" column. |
| **Kindle Optimization** | Uses `transform: rotate(-90deg)` to force landscape mode on portrait-only browsers. |

---

## 4. Configuration & Deployment

### Deployment via Plash (macOS)
1.  Save the code as `weather.html`.
2.  Open **Plash**.
3.  Select **Add Local Website** and choose your file.
4.  **Weather Now** will appear as a borderless desktop widget.

### Deployment via Kindle
1.  Host the `.html` file on a local server or public URL.
2.  Open the **Experimental Browser** on the Kindle.
3.  Navigate to the URL.
4.  The dashboard will automatically rotate and scale to fit the screen.

### Modifying Location
To change the location, update the constants at the top of the `fetchWeather` function:
```javascript
const lat = 56.60712432274488;
const lon = -3.0858753489219812;
```

---

## 5. Maintenance & Troubleshooting

* **API Usage:** Open-Meteo is free for non-commercial use (up to 10,000 requests/day).
* **Time Sync:** **Weather Now** determines `hr_now` by matching the system clock to the nearest `T00:00` timestamp in the API array, ensuring data alignment even if the local clock drifts slightly.
* **Wind Discrepancies:** Ensure the `&wind_speed_unit=mph` parameter is present in the API URL to avoid metric/imperial calculation errors.
