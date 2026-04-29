This is the official documentation for the **Kindle Link Index**, a lightweight, high-contrast web portal designed specifically for the Amazon Kindle’s experimental browser.

---

# Kindle Link Index: Documentation
**URL:** [https://alexroddie.github.io/](https://alexroddie.github.io/)  
**Author:** Alex Roddie  
**Purpose:** A minimalist, E-Ink optimized gateway for outdoor weather data and essential mountain links.

---

## 1. Overview
The Kindle Link Index serves as a "home page" for Kindle users who need quick access to critical information while in the field. Because the Kindle’s experimental browser has limited processing power and a grayscale E-Ink display, this site uses minimal JavaScript, zero heavy assets, and high-contrast CSS to ensure readability and speed.

## 2. Key Pages

### 🏠 Home Index
The main landing page features a vertical list of large, tappable links. This acts as a centralized hub to prevent the user from having to type complex URLs into the Kindle’s slow keyboard.
* **Design:** Large text, generous spacing (to prevent accidental taps), and no images.
* **Primary Links:** Direct paths to the Weather Now and Mountain Dashboard pages, along with external text-only resources.

### 🌤 Weather Now
A dedicated page for localized, real-time weather conditions.
* **Features:** Displays current temperature, wind speed, and a simplified 3-day forecast.
* **Optimization:** Uses a "mobile-first" and "E-Ink first" layout. Data is presented in a clear, tabular, or list-based format that renders perfectly in grayscale.
* **Data Source:** (Usually configured for a specific home location or region, such as Meigle/Ardler or the Scottish Highlands).

### 🏔 Mountain Dashboard
The most feature-rich page, specifically designed for hikers and mountaineers. It aggregates critical mountain safety data into a single view.
* **Content Sections:**
    * **MWIS Forecasts:** Direct links to the Mountain Weather Information Service PDF/text summaries.
    * **Met Office Mountain:** Links to regional summit forecasts.
    * **Avalanche Reports (SAIS):** Quick links to winter stability reports (seasonal).
    * **River Levels:** Vital for assessing ford crossings in the backcountry.
* **Kindle Optimization:** The dashboard strips away navigation bars and sidebars from external sources where possible, focusing purely on the text and data.

---

## 3. Kindle Optimization Features

To cater to the unique constraints of the Kindle (e.g., Paperwhite, Oasis, or Scribe), the site employs the following:
* **System Fonts:** Uses basic `serif` or `sans-serif` stacks to avoid loading external web fonts.
* **No Fixed Elements:** Avoiding "sticky" headers that often glitch during scrolling on E-Ink.
* **Grayscale Palette:** Every element is defined in pure black (#000), white (#FFF), or high-contrast grey to ensure no information is lost when the browser converts colors.
* **Low Payload:** The entire site is typically under 50KB, allowing for fast loading even on 3G or weak 4G tethered connections.

---

## 4. How to Use on Your Kindle

1.  **Open the Browser:** On your Kindle, go to `Menu` (three dots) -> `Web Browser`.
2.  **Enter the URL:** Type in `alexroddie.github.io`.
3.  **Bookmark It:** Once loaded, tap the Menu icon again and select **Bookmark this Page**.
4.  **Set as Homepage:** (Optional) Some Kindle versions allow you to set a default page; setting this as your home makes it your "outdoor dashboard" every time you open the browser.

---

## 5. Technical Details
* **Hosting:** Hosted on GitHub Pages for 100% uptime and SSL security.
* **Framework:** Built with raw HTML5 and CSS3 (No heavy frameworks like Bootstrap or React).
* **Maintenance:** To update links or the Weather Now location, the `index.html` and `weather.html` files must be edited in the GitHub repository.

---

## 6. Resources & External Links
The dashboard provides curated shortcuts to:
* [MWIS](https://www.mwis.org.uk/)
* [Met Office Mountain Weather](https://www.metoffice.gov.uk/weather/specialist-forecasts/mountain)
* [SAIS Avalanche Reports](https://www.sais.gov.uk/)
* [Septentrio Weather](https://septentrio.net/) (If applicable)

---
*Documentation generated for Alex Roddie's Kindle Index Project.*
