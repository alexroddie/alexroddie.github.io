# Kindle Link Index

**URL:** [https://alexroddie.github.io/](https://alexroddie.github.io/)  
**Author:** Alex Roddie  
**Purpose:** A minimalist, E-Ink optimized gateway for outdoor weather data and essential mountain links.

> **⚠️ WARNING:** > Please do not edit any of these files. They are for Alex Roddie's personal use only.

---

## 1. Overview
The Kindle Link Index serves as a home page for Kindle users who need quick access to critical information while in the field. Because the Kindle’s experimental browser has limited processing power and a grayscale E-Ink display, this site uses minimal JavaScript, zero heavy assets, and high-contrast CSS to ensure readability and speed.

## 2. Key Pages

### Home Index
The main landing page features a vertical list of large, tappable links. This acts as a centralized hub to prevent the user from having to type complex URLs into the Kindle’s slow keyboard.
* **Design:** Large text, generous spacing (to prevent accidental taps), and no images.
* **Primary Links:** Direct paths to the Weather Now and Mountain Dashboard pages, along with external text-only resources.

### Weather Now `weathernow/index.html`
A custom, highly intelligent weather dashboard built specifically for E-Ink displays (like TRMNL and Kindle).
* **Features:** Displays current temperature, wind speed, dynamic forecasting summaries, and intelligent array slicing for future time-blocks.
* **Optimization:** Completely static and pre-rendered. Zero client-side JavaScript fetching is required, making it load instantly on slow E-Ink processors.
* **Data Source & Architecture:** Powered by the Open-Meteo API. To bypass API rate limits, a local Synology NAS fetches the data every 15 minutes, generates this static HTML file, and deploys it automatically.
* **Documentation:** [Readme.html](https://alexroddie.github.io/weathernow/Readme.html)

### Mountain Dashboard `mountainweather/index.html`
The most feature-rich page, specifically designed for hikers and mountaineers. It aggregates critical mountain safety data into a single view.
* **Content Sections:**
  * **MWIS Forecasts:** Direct links to the Mountain Weather Information Service text summaries.
  * **Avalanche Reports (SAIS):** Quick links to winter stability reports (seasonal).
* **Kindle Optimization:** The dashboard strips away navigation bars and sidebars from external sources where possible, focusing purely on the text and data.
* **Documentation:** [Readme.html](https://alexroddie.github.io/mountainweather/Readme.html)

## 3. Kindle Optimization Features
To cater to the unique constraints of the Kindle, the site employs the following:
* **System Fonts:** Uses basic serif or sans-serif stacks to avoid loading external web fonts.
* **No Fixed Elements:** Avoiding "sticky" headers that often glitch during scrolling on E-Ink.
* **Grayscale Palette:** Every element is defined in pure black (#000), white (#FFF), or high-contrast grey to ensure no information is lost when the browser converts colors.
* **Low Payload:** The entire site is typically under 50KB, allowing for fast loading even on 3G or weak 4G tethered connections.

## 4. How to Use on Your Kindle
1. **Open the Browser:** On your Kindle, go to `Menu` (three dots) -> `Web Browser`.
2. **Enter the URL:** Type in `alexroddie.github.io`.
3. **Bookmark It:** Once loaded, tap the Menu icon again and select **Bookmark this Page**.
4. **Set as Homepage:** (Optional) Some Kindle versions allow you to set a default page; setting this as your home makes it your "outdoor dashboard" every time you open the browser.

## 5. Technical Details
* **Hosting:** Hosted on GitHub Pages for 100% uptime and SSL security.
* **Framework:** Built with raw HTML5 and CSS3 (No heavy frameworks like Bootstrap or React).
* **Maintenance:** To update links on the main index or Mountain Dashboard, edit the files directly in the GitHub repository. **Crucially, Weather Now files must ONLY be edited locally on the Synology NAS**, as any direct GitHub edits to the `weathernow` folder will be permanently overwritten every 15 minutes by the automated deployment script.

## 6. Resources & External Links
* The dashboard provides curated shortcuts to various external resources.
* Edit the `index.html` file to adapt these.

---
*Documentation for Alex Roddie's Kindle Index Project.*
