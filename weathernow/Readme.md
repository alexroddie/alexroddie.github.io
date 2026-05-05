# Documentation: Weather Now
**Dual-Platform Weather Reporting Solution**

## Project Overview
**Weather Now** is a minimalist weather reporting system designed for high-contrast E-Ink displays and desktop widgets. It serves two primary deployment paths:
1.  **TRMNL (Liquid):** A server-side implementation for dedicated E-Ink hardware.
2.  **Standalone (HTML/JS):** A responsive web application optimized for macOS (Plash), Amazon Kindle, and mobile devices.

The system interfaces with the **Open-Meteo API**, prioritizing "Next-Step" context (Later, Overnight, Tomorrow) over redundant current data.

---

## 1. Implementation Path A: TRMNL (Liquid)
Designed for the TRMNL hardware backend using the Liquid templating language.

### A. Environment Configuration
*   **Data Source:** Open-Meteo API.
*   **Coordinates:** `56.6071, -3.0858` (Castleton of Eassie).
*   **Timezone Logic:** Since the TRMNL backend operates on UTC, the code includes a manual **BST/GMT offset block** that identifies the last Sunday of March and October to shift `hr_now` correctly.

### B. Deployment
1.  Create a **New Private Plugin** in the TRMNL Dashboard.
2.  Set the Data Source to the Open-Meteo URL.
3.  Paste the Liquid markup.
4.  Ensure all condition mapping logic (`get_cond`) is included to translate Open-Meteo codes into plain-English strings.

---

## 2. Implementation Path B: Standalone (Responsive HTML/JS)
A self-contained application that adapts its layout based on the viewing device.

### A. Technical Architecture
*   **Desktop View:** Locked at a fixed **840 × 480** canvas for TRMNL parity and macOS Plash widgets.
*   **Responsive Reflow:** Automatically switches to a vertical stack on screens ≤ 840px (Mobile/Kindle).
*   **Visual Consistency:** Uses two 3px thick black lines to bound the hourly scale. All "mystery" grey lines and internal dividers are stripped for a clean aesthetic.
*   **Black Glyph Lock:** Uses the Unicode Variation Selector-15 (`&#xFE0E;`) to force E-Ink style black sun glyphs on mobile devices that would otherwise render yellow emojis.

### B. Mobile Optimization
*   **Hero Density:** Current temperature and conditions are placed side-by-side with Rain and Wind data to maximize vertical space.
*   **Symmetrical Grid:** The hourly scale uses a **2 × 3 grid**. The "Later" block is dynamically reformatted into a 5-line stack to match the hourly cells, ensuring a perfectly even grid.

---

## 3. Core Features & "Secret Sauce" Logic
Both versions share a "Blindfold" architecture to ensure the dashboard remains informative.

### A. The "Blindfold" Methodology
To prevent repeating data already visible in the 5-hour hourly scale, all secondary scans (Later and Overnight) begin strictly at `hr_now + 6`.

### B. Sectional Logic
*   **"Later" Block:** 
    *   *Desktop:* Shows a 3-line horizontal summary.
    *   *Mobile:* Shows a 5-line symmetrical stack.
*   **"Overnight" Scan:** Scans from the end of the day through 6:00 AM the following morning to identify the lowest temperature and any "first-strike" precipitation.
*   **"Tomorrow" Vibe Track:** Analyzes daylight hours (Sunrise to Sunset) to determine if the day is "Sunny," "Cloudy," or "Rainy" (if ≥ 3 hours of precipitation are predicted).

---
*Documentation updated: May 2026*
