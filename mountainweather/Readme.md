# Mountain Dashboard Documentation
*Automated Mountain Weather & Avalanche Reporting System*

**Mountain Dashboard** is a lightweight, automated weather scraping and presentation system designed to provide concise mountain weather forecasts and avalanche reports for specialized devices, specifically **Kindle e-readers** and **TRMNL e-paper displays**, as well as mobile browsers.

---

## 1. System Overview

Mountain Dashboard operates as a "serverless" application using GitHub's infrastructure. It consists of three primary layers:

1. **The Scraper (Python):** A script (`build.py`) that extracts text and images from the Mountain Weather Information Service (MWIS) and the Scottish Avalanche Information Service (SAIS).
2. **The Automation (GitHub Actions):** A workflow (`update.yml`) that triggers the scraper on a fixed schedule and handles the deployment of updated files.
3. **The Hosting (GitHub Pages):** A public web server that hosts the generated HTML files for consumption by external devices.

---

## 2. Technical Components

### 2.1 The Python Scraper (`mountainweather/build.py`)
The core logic performs the following tasks:

* **Data Retrieval:** Uses the `requests` library to fetch HTML from MWIS and SAIS.
* **Parsing:** Uses `BeautifulSoup4` to extract the overarching Area Summary and Planning Outlook, implementing dynamic character-count thresholds to automatically scale text sizes to fit hardware boundaries.
* **Synoptic Chart Extraction:** Identifies and downloads the current synoptic weather chart URL.
* **Unified Layout Generation:** Generates a single `trmnl.html` file that serves both TRMNL and mobile devices. It sets a strict, fixed 800x480 two-pane layout for the TRMNL device by default. It also embeds a CSS `@media` query "escape hatch" that automatically triggers on narrower screens (like Kindles or smartphones) to stack the content vertically, enlarge reading fonts, and reveal native HTML accordion menus for additional regional forecast links.
* **Timezone Handling:** Uses `zoneinfo` (Europe/London) to ensure timestamps are accurate to the UK mountain environment.

### 2.2 The Automation Workflow (`.github/workflows/update.yml`)
The workflow is configured to ensure the dashboard is updated multiple times daily:

* **Schedule:** Triggered via `cron` at **04:30, 10:30, 16:30, and 17:30 UTC**.
* **Manual Trigger:** Supports `workflow_dispatch` for immediate updates.
* **The 60-Day Bypass:** Uses a `PERSONAL_ACCESS_TOKEN` for Git pushes to mimic human activity, preventing GitHub from disabling the scheduled workflow due to inactivity.

### 2.3 Hosting
Files are hosted via **GitHub Pages**. Once the workflow pushes the generated HTML files to the `main` branch, they are instantly live at your GitHub Pages URL.

---

## 3. Installation and Setup

### 3.1 Repository Structure
```text
.
├── .github/
│   └── workflows/
│       └── update.yml      # The automation logic
└── mountainweather/
    ├── build.py            # The scraping logic
    └── trmnl.html          # (Auto-generated unified dashboard)
