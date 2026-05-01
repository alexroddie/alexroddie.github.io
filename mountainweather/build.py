import requests, datetime, re
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

urls = {
    'mwis_west': 'https://www.mwis.org.uk/forecasts/scottish/west-highlands/text',
    'mwis_cairngorms': 'https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text',
    'mwis_se_highlands': 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text',
    'mwis_nw_highlands': 'https://www.mwis.org.uk/forecasts/scottish/the-northwest-highlands/text',
    'mwis_synoptic': 'https://www.mwis.org.uk/forecasts/synoptic-charts',
    'sais_n_cairngorms': 'https://www.sais.gov.uk/northern-cairngorms/',
    'sais_s_cairngorms': 'https://www.sais.gov.uk/southern-cairngorms/',
    'sais_lochaber': 'https://www.sais.gov.uk/lochaber/',
    'sais_glencoe': 'https://www.sais.gov.uk/glencoe/',
    'sais_creag_meagaidh': 'https://www.sais.gov.uk/creag-meagaidh/',
    'sais_torridon': 'https://www.sais.gov.uk/torridon/'
}

headers = {'User-Agent': 'Mozilla/5.0'}
data, planning_outlook, area_summary, synoptic_url = {}, "Outlook unavailable.", "Summary unavailable.", None
trmnl_se_date = datetime.datetime.now(ZoneInfo("Europe/London")).strftime('%A')

def format_text(lines):
    ignore = ["how windy?", "how wet?", "cloud on the hills?", "how cold?", "freezing level", "headline for", "chance of cloud free"]
    cleaned = []
    for l in [line.strip() for line in lines if line.strip()]:
        l = l.lstrip('.').lstrip(':').strip() # Remove accidental header artifacts
        if l and not any(p in l.lower() for p in ignore):
            cleaned.append(l if l[-1] in ".!?" else l + ".")
    return " ".join(cleaned)

# 1. SCRAPE SYNOPTIC CHART (Structural search)
try:
    res = requests.get(urls['mwis_synoptic'], headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src', '')
        # Identify the synoptic chart by content, excluding common UI logos
        if any(x in src.lower() for x in ['chart', 'synoptic']) and 'logo' not in src.lower():
            synoptic_url = "https://www.mwis.org.uk" + src if src.startswith('/') else src
            break
except: pass

# 2. SCRAPE MWIS DATA (Regex-Hardened)
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands', 'mwis_nw_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Flatten text to one searchable string to handle shifting line breaks
        full_page_text = ' '.join(soup.get_text(separator=' ').split())

        # --- SUMMARY SCRAPER (Regex) ---
        if area_summary == "Summary unavailable.":
            # Captures everything between the Summary header and the next logical section
            match = re.search(r"summary for all mountain areas(.*?)(headline for|planning outlook)", full_page_text, re.IGNORECASE)
            if match:
                area_summary = match.group(1).strip().lstrip('.').lstrip(':').strip()

        # --- OUTLOOK SCRAPER (Regex) ---
        if planning_outlook == "Outlook unavailable.":
            # Captures everything from the header until the very end of the page content
            match = re.search(r"planning outlook(.*?)(viewing forecast for|©|$)", full_page_text, re.IGNORECASE)
            if match:
                planning_outlook = match.group(1).strip().lstrip('.').lstrip(':').strip()

        # --- REGIONAL DAILY PARSING (Flexible Partial Match) ---
        lines = [l.strip() for l in soup.get_text(separator='\n').split('\n') if l.strip()]
        days, cur = [], None
        for l in lines:
            low_l = l.lower()
            if "viewing forecast for" in low_l:
                if cur: days.append(cur)
                cur = {"date": "Today", "headline":[], "wind":[], "wet":[], "cloud":[], "chance_cloud_free":[], "temp":[], "freezing_level":[]}
                sec = "date"
                continue
            if cur:
                if "headline for" in low_l: sec = "headline"
                elif "how windy?" in low_l: sec = "wind"
                elif "how wet?" in low_l: sec = "wet"
                elif "cloud on the hills?" in low_l: sec = "cloud"
                elif "chance of cloud free" in low_l: sec = "chance_cloud_free"
                elif "how cold?" in low_l: sec = "temp"
                elif "freezing level" in low_l: sec = "freezing_level"
                elif any(x in low_l for x in ["summary", "effect", "sunshine", "planning"]): sec = "ignore"
                elif sec == "date":
                    for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
                        if d in l: cur["date"] = d; sec = "ignore"; break
                elif sec != "ignore": cur[sec].append(l)
        if cur: days.append(cur)
        
        if key == 'mwis_se_highlands' and len(days) > 0:
            trmnl_se_date = days[0].get('date', 'Today')
        
        # Build Kindle content blocks
        html = ""
        for i, d in enumerate(days[:3]):
            head = format_text(d['headline'])
            content = f"<p><em>{head.rstrip('.')}</em>.</p>" if head else ""
            content += "<ul>"
            for lbl, fld in [("Wind","wind"),("Wet","wet"),("Cloud","cloud"),("Chance of Munros","chance_cloud_free"),("Temp","temp"),("Freezing","freezing_level")]:
                val = format_text(d[fld])
                if val: content += f"<li><strong>{lbl}:</strong> {val}</li>"
            content += "</ul>"
            if i > 0: html += f"<div class='inner-day'><div class='inner-day-header'><strong>{d['date']}</strong></div><div class='inner-content'>{content}</div></div>"
            else: html += f"<div class='day-one'><strong>{d['date']}</strong>{content}</div>"
        data[key] = html
    except: data[key] = "Region data error."

# 3. SCRAPE SAIS (Avalanche)
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe', 'sais_creag_meagaidh', 'sais_torridon']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        if "finished" in soup.get_text().lower(): data[key] = "Season finished."
        else:
            h = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = h.text.strip() if h else "No data."
    except: data[key] = "Error."

# 4. GENERATE TIMESTAMPS
now = datetime.datetime.now(ZoneInfo("Europe/London"))
suff = 'th' if 11<=now.day<=13 else {1:'st',2:'nd',3:'rd'}.get(now.day%10, 'th')
ts = now.strftime(f'%A, %B {now.day}{suff} at %I.%M%p').lower().lstrip('0')
chart_html = f'<div style="text-align:center;margin-bottom:20px;"><img src="{synoptic_url}" style="max-width:100%;height:auto;"/></div>' if synoptic_url else ""

# 5. GENERATE KINDLE HTML (index.html)
kindle_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{{font-family:Georgia,serif;padding:10px;line-height:1.5;background:#fff;color:#000;max-width:94%;margin:0 auto;}}
h1{{text-align:center;border-bottom:3px solid #000;padding-bottom:10px;margin-bottom:20px;}}
.region{{border:2px solid #000;margin-bottom:20px;padding:0;}}
summary{{cursor:pointer;background:#000;color:#fff;padding:8px 12px;font-size:1.2em;font-weight:bold;display:block;}}
.content{{padding:15px;}}
.inner-day{{border-top:1px dashed #000;margin-top:5px;padding-top:5px;}}
.inner-day-header{{background:#eee;padding:4px 15px;font-weight:bold;}}
.status{{text-align:center;font-size:0.9em;margin-bottom:20px;}}
</style></head><body>
<h1>Mountain Dashboard</h1><div class="status">Updated {ts}</div>
{chart_html}
<details class="region" open><summary>Summary & Outlook</summary><div class="content">
<p>{area_summary}</p>
<div class="inner-day"><div class="inner-day-header">Planning Outlook</div><div style="padding:10px;">{planning_outlook}</div></div>
</div></details>
<details class="region"><summary>SE Highlands</summary><div class="content">{data.get('mwis_se_highlands', 'N/A')}</div></details>
<details class="region"><summary>Cairngorms</summary><div class="content">{data.get('mwis_cairngorms', 'N/A')}</div></details>
<details class="region"><summary>SAIS Avalanche</summary><div class="content"><ul>
<li><strong>S Cairngorms:</strong> {data.get('sais_s_cairngorms','N/A')}</li>
<li><strong>N Cairngorms:</strong> {data.get('sais_n_cairngorms','N/A')}</li>
<li><strong>Glencoe:</strong> {data.get('sais_glencoe','N/A')}</li>
</ul></div></details></body></html>"""

with open("index.html", "w", encoding="utf-8") as f: f.write(kindle_tmpl)

# 6. GENERATE TRMNL HTML (trmnl.html)
total_chars = len(area_summary) + len(planning_outlook)
t_body_size, t_header_size = "11pt", "17px"
if total_chars > 1200: t_body_size, t_header_size = "9pt", "15px"
elif total_chars > 800: t_body_size, t_header_size = "10pt", "16px"

trmnl_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{{margin:0;padding:0;width:800px;height:480px;font-family:Georgia,serif;display:flex;}}
.left{{width:50%;padding:25px;display:flex;align-items:center;justify-content:center;}}
.left img{{max-width:100%;max-height:100%;object-fit:contain;}}
.right{{width:50%;padding:25px;display:flex;flex-direction:column;}}
.header{{font-size:{t_header_size};font-weight:bold;margin-bottom:8px;}}
.body{{font-size:{t_body_size};line-height:1.2;margin-bottom:15px;}}
</style></head><body>
<div class="left"><img src="{synoptic_url}" /></div>
<div class="right">
    <div class="header">{trmnl_se_date}</div>
    <div class="body">{area_summary}</div>
    <div class="body">{planning_outlook}</div>
</div></body></html>"""

with open("trmnl.html", "w", encoding="utf-8") as f: f.write(trmnl_tmpl)
