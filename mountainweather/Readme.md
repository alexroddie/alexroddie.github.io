# Mountain Dashboard Documentation

**Mountain Dashboard** is a lightweight, automated weather scraping and presentation system designed to provide concise mountain weather forecasts and avalanche reports for specialized devices, specifically **Kindle e-readers** and **TRMNL e-paper displays**, as well as mobile browsers.

---

## 1. System Overview

Mountain Dashboard operates as a "serverless" application using GitHub's infrastructure. It consists of three primary layers:

1.  **The Scraper (Python):** A script (`build.py`) that extracts text and images from the Mountain Weather Information Service (MWIS) and the Scottish Avalanche Information Service (SAIS).
2.  **The Automation (GitHub Actions):** A workflow (`update.yml`) that triggers the scraper on a fixed schedule and handles the deployment of updated files.
3.  **The Hosting (GitHub Pages):** A public web server that hosts the generated HTML files for consumption by external devices.

---

## 2. Technical Components

### 2.1 The Python Scraper (`mountainweather/build.py`)
The core logic performs the following tasks:
* **Data Retrieval:** Uses the `requests` library to fetch HTML from MWIS and SAIS.
* **Parsing:** Uses `BeautifulSoup4` to extract specific forecast fields (Wind, Precipitation, Cloud, Temperature, and Freezing Level).
* **Synoptic Chart Extraction:** Identifies and downloads the current synoptic weather chart URL.
* **Kindle Optimization:** Generates an `index.html` file using `<details>` and `<summary>` tags. To fix a known Kindle rendering bug, heading styles (background, padding, and font) are applied directly to the `<summary>` element to prevent "double-height" black bars.
* **TRMNL Optimization:** Generates a `trmnl.html` file with a fixed 800x480 resolution, featuring a two-pane layout (Synoptic Chart on the left, SE Highlands summary and Planning Outlook on the right).
* **Timezone Handling:** Uses `zoneinfo` (Europe/London) to ensure timestamps are accurate to the UK mountain environment.

### 2.2 The Automation Workflow (`.github/workflows/update.yml`)
The workflow is configured to ensure the dashboard is updated multiple times daily:
* **Schedule:** Triggered via `cron` at **04:30, 10:30, 16:30, and 17:30 UTC**.
* **Manual Trigger:** Supports `workflow_dispatch` for immediate updates via the GitHub UI.
* **The 60-Day Bypass:** GitHub normally disables scheduled workflows in public repositories after 60 days of inactivity. Mountain Dashboard bypasses this by using a `PERSONAL_ACCESS_TOKEN` for Git pushes, which GitHub interprets as regular "human" activity.

### 2.3 Hosting
Files are hosted via **GitHub Pages**. Once the workflow pushes the generated HTML files to the `main` branch, they are instantly live at your GitHub Pages URL (e.g., `https://[username].github.io/mountainweather/`).

---

## 3. Installation and Setup

### 3.1 Repository Structure
Ensure your GitHub repository is structured as follows:
```text
.
├── .github/
│   └── workflows/
│       └── update.yml      # The automation logic
└── mountainweather/
    ├── build.py            # The scraping logic
    ├── index.html          # (Auto-generated Kindle dashboard)
    └── trmnl.html          # (Auto-generated TRMNL dashboard)
```

### 3.2 GitHub Secrets
To ensure the automation never stops, you must configure a Personal Access Token:
1.  Generate a **Classic PAT** in GitHub Settings with `repo` permissions.
2.  In your repository, go to **Settings > Secrets and variables > Actions**.
3.  Add a new secret named `PERSONAL_ACCESS_TOKEN` and paste your token.

### 3.3 Enabling Hosting
1.  Go to **Settings > Pages**.
2.  Set the **Source** to "Deploy from a branch".
3.  Select the **main** branch and the `/(root)` folder.
4.  Click **Save**. Your dashboard will be live at the provided URL.

---

## 4. Device Configuration

### 4.1 Kindle E-Reader
Point the Kindle's "Experimental Browser" to your `index.html` URL.
* **Layout:** The page uses a 94% width with 3% margins for optimal e-ink readability.
* **Interaction:** Tapping the black headers (Summary, SE Highlands, etc.) will expand or collapse the sections.
* **Visuals:** Headings appear as single-height black bars with white text, optimized for the Kindle's limited CSS support.

### 4.2 TRMNL Display
Configure your TRMNL device (or a Custom App) to pull from your `trmnl.html` URL.
* **Refresh Rate:** Match the TRMNL refresh rate to the update schedule (e.g., every 1-2 hours).
* **Scaling:** The 800x480 fixed layout ensures no scrolling is required on the device.

---

## 5. Maintenance and Troubleshooting

### 5.1 Scheduling Delays
GitHub Actions are a "best effort" service. Scheduled runs may be delayed by 15 to 90 minutes depending on server load. This is a platform limitation of GitHub and does not indicate a bug in Mountain Dashboard.

### 5.2 Scraping Failures
If MWIS or SAIS significantly change their website structure:
1.  The workflow may report a failure in the **Actions** tab.
2.  Check the logs to identify which BeautifulSoup selector (e.g., `.hazard-level h2`) is failing.
3.  Update the `urls` or the parsing logic in `build.py` accordingly.

### 5.3 Deployment Errors
If the dashboard is not updating:
1.  Verify that your `PERSONAL_ACCESS_TOKEN` has not expired.
2.  Ensure GitHub Pages is still pointed to the `main` branch.
3.  Check that the script has the necessary permissions to write to the repository.
