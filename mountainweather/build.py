import requests, datetime, re
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# ... (urls and headers remain the same as your current version)

def format_text(lines):
    ignore = ["how windy?", "how wet?", "cloud on the hills?", "how cold?", "freezing level", "headline for", "chance of cloud free"]
    cleaned = []
    for l in [line.strip() for line in lines if line.strip()]:
        # Remove any leading punctuation that might come from splitting headers
        l = l.lstrip('.').lstrip(':').strip()
        if l and not any(p in l.lower() for p in ignore):
            cleaned.append(l if l[-1] in ".!?" else l + ".")
    return " ".join(cleaned)

# 1. Scrape Synoptic Chart
# ... (same as your current version)

# 2. Scrape MWIS Regions
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands', 'mwis_nw_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Use a consistent separator and clean whitespace
        text_content = soup.get_text(separator='\n')
        lines = [l.strip() for l in text_content.split('\n') if l.strip()]
        
        # --- Area Summary Scraper (Improved same-line capture) ---
        if area_summary == "Summary unavailable.":
            sum_l, sum_cap = [], False
            trigger = "summary for all mountain areas"
            for l in lines:
                if not sum_cap and trigger in l.lower():
                    sum_cap = True
                    # Capture everything on the same line AFTER the trigger
                    parts = re.split(trigger, l, flags=re.IGNORECASE)
                    if len(parts) > 1 and parts[1].strip():
                        sum_l.append(parts[1].strip())
                    continue
                if sum_cap:
                    if any(x in l.lower() for x in ["headline for", "planning outlook", "looking ahead"]): 
                        sum_cap = False; break
                    sum_l.append(l)
            if sum_l: area_summary = format_text(sum_l)

        # --- Planning Outlook Scraper (Improved same-line capture) ---
        if planning_outlook == "Outlook unavailable.":
            out_l, cap = [], False
            # Check for both common headers
            for l in lines:
                found_trigger = None
                if "planning outlook" in l.lower(): found_trigger = "planning outlook"
                elif "looking ahead" in l.lower(): found_trigger = "looking ahead"
                
                if not cap and found_trigger:
                    cap = True
                    # Capture everything on the same line AFTER the trigger
                    parts = re.split(found_trigger, l, flags=re.IGNORECASE)
                    if len(parts) > 1 and parts[1].strip():
                        out_l.append(parts[1].strip())
                    continue
                if cap:
                    # Structural stop: end of text-only page content
                    if any(x in l.lower() for x in ["viewing forecast for", "copyright"]): 
                        cap = False; break
                    out_l.append(l)
            if out_l: planning_outlook = format_text(out_l)

# ... (The rest of the script: SAIS scraping, HTML generation, and dynamic scaling remains unchanged)
