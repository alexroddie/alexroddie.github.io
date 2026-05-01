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
trmnl_se_date = "Today"

def sanitize_mwis_text(text):
    """Aggressively eradicates dynamic junk and sub-questions before parsing."""
    # 1. Kill dynamic timestamps (e.g., "Fri 1st May 26 at 2:58PM")
    text = re.sub(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\s+at\s+\d{1,2}:\d{2}[AP]M", " ", text, flags=re.IGNORECASE)
    # 2. Kill the sub-questions that bleed into main fields
    text = re.sub(r"Effect of the wind on you\??", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Sunshine and air clarity\??", " ", text, flags=re.IGNORECASE)
    # 3. Kill repetitive region names and preamble
    text = re.sub(r"Viewing Forecast For", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Southeastern Highlands|The Northwest Highlands|West Highlands|Cairngorms NP and Monadhliath", " ", text, flags=re.IGNORECASE)
    # 4. Kill general footer junk
    text = re.sub(r"www\.mwis\.org\.uk|©\s*Copyright|Forecast issued|Last updated", " ", text, flags=re.IGNORECASE)
    
    # Normalize spacing
    return ' '.join(text.split())

def clean_val(val):
    val = re.sub(r"^[\.\:\?\-\s]+", "", val).strip()
    if not val: return ""
    return val if val[-1] in ".!?" else val + "."

# 1. Scrape Synoptic Chart
try:
    res = requests.get(urls['mwis_synoptic'], headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if ('chart' in src.lower() or 'synoptic' in src.lower()) and 'logo' not in src.lower():
            synoptic_url = "https://www.mwis.org.uk" + src if src.startswith('/') else src
            break
except: pass

# 2. Scrape MWIS Regions
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands', 'mwis_nw_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Pull raw text and immediately run the sanitizer
        raw_text = soup.get_text(separator=' ')
        clean_text = sanitize_mwis_text(raw_text)

        # Global Summary & Outlook (Using flexible fallbacks)
        if area_summary == "Summary unavailable.":
            m_sum = re.search(r"Summary for all mountain areas\.?(.*?)(?:Planning Outlook|Looking Ahead|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", clean_text, re.IGNORECASE)
            if m_sum: area_summary = clean_val(m_sum.group(1))
            
        if planning_outlook == "Outlook unavailable.":
            m_out = re.search(r"(?:Planning Outlook|Looking Ahead)\.?(.*?)(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", clean_text, re.IGNORECASE)
            if m_out: planning_outlook = clean_val(m_out.group(1))

        # Split into individual days using strictly defined Date Regex
        date_regex = r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})"
        
        # This splits the massive string into chunks starting with the date
        day_chunks = re.split(date_regex, clean_text, flags=re.IGNORECASE)
        
        days = []
        # day_chunks[0] is the preamble/summary. The rest are Date, Content, Date, Content...
        for i in range(1, len(day_chunks)-1, 2):
            if len(days) >= 3: break
            
            date_str = day_chunks[i].strip()
            chunk_text = day_chunks[i+1]
            
            day_dict = {"date": date_str, "headline": "", "wind": "", "wet": "", "cloud": "", "chance": "", "temp": "", "freezing": ""}
            
            # Map out where each section starts in this chunk
            metrics = [
                ("wind", r"How windy\?(?:\s*\([^\)]+\))?"),
                ("wet", r"How Wet\?"),
                ("cloud", r"Cloud on the hills\?"),
                ("chance", r"Chance of cloud free[^\?]*\?"),
                ("temp", r"How Cold\?(?:\s*\([^\)]+\))?"),
                ("freezing", r"Freezing Level\.?")
            ]
            
            positions = []
            for key_name, reg in metrics:
                m = re.search(reg, chunk_text, re.IGNORECASE)
                if m: positions.append({"key": key_name, "start": m.start(), "end": m.end()})
            
            positions.sort(key=lambda x: x["start"])
            
            # Extract Headline (Everything before the very first header, usually "How windy?")
            if positions:
                hl_raw = chunk_text[:positions[0]["start"]].strip()
                day_dict["headline"] = clean_val(re.sub(r"Headline for[^\.]*\.", "", hl_raw, flags=re.IGNORECASE))
            
            # Extract Metrics (Stop reading exactly where the next metric begins)
            for idx, pos in enumerate(positions):
                val_start = pos["end"]
                val_end = positions[idx+1]["start"] if idx+1 < len(positions) else len(chunk_text)
                day_dict[pos["key"]] = clean_val(chunk_text[val_start:val_end])
                
            days.append(day_dict)

        if key == 'mwis_se_highlands' and len(days) > 0:
            trmnl_se_date = days[0].get('date', 'Today')

        # Build HTML
        html = ""
        for i, d in enumerate(days):
            content = f"<p><em>{d['headline']}</em></p>" if d['headline'] else ""
            content += "<ul>"
            for lbl, val in [("Wind", d["wind"]), ("Wet", d["wet"]), ("Cloud", d["cloud"]), ("Chance of cloud-free Munros", d["chance"]), ("Temp", d["temp"]), ("Freezing level", d["freezing"])]:
                if val: content += f"<li><strong>{lbl}:</strong> {val}</li>"
            content += "</ul>"
            if i > 0: html += f"<div class='inner-day'><div class='inner-day-header'><strong>{d['date']}</strong></div><div class='inner-content'>{content}</div></div>"
            else: html += f"<div class='day-one'><strong>{d['date']}</strong>{content}</div>"
            
        if not html: html = "<p>Data format altered by MWIS. Scraper updating.</p>"
        data[key] = html
    except Exception as e:
        data[key] = f"Error fetching region. ({e})"

# 3. Scrape SAIS
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe', 'sais_creag_meagaidh', 'sais_torridon']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        h = soup.select_one('.hazard-level h2')
        if h: data[key] = h.text.strip()
        else:
            text = soup.get_text().lower()
            if "avalanche hazard will be low" in text: data[key] = "Low"
            elif "avalanche hazard will be moderate" in text: data[key] = "Moderate"
            elif "avalanche hazard will be considerable" in text: data[key] = "Considerable"
            elif "avalanche hazard will be high" in text: data[key] = "High"
            else: data[key] = "No data / Season finished."
    except: data[key] = "Error."

# 4. Generate Timestamps
now = datetime.datetime.now(ZoneInfo("Europe/London"))
suff = 'th' if 11<=now.day<=13 else {1:'st',2:'nd',3:'rd'}.get(now.day%10, 'th')
time_str = now.strftime('%I.%M%p').lower().lstrip('0')
ts = now.strftime(f'%A, %B {now.day}{suff} at {time_str}')
chart = f'<div class="chart-container" style="text-align:center;margin-bottom:20px;"><a href="{urls["mwis_synoptic"]}"><img src="{synoptic_url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"/></a></div>' if synoptic_url else ""

# 5. Generate Kindle HTML (index.html)
kindle_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{{font-family:Georgia,serif;padding:10px;line-height:1.5;background:#fff;color:#000;max-width:94%;margin:0 auto;}}
h1{{text-align:center;border-bottom:3px solid #000;padding-bottom:10px;margin-bottom:20px;line-height:1.1;}}
.region,details.region{{border:2px solid #000;margin-bottom:20px;padding:0;}}
summary{{cursor:pointer;background:#000;color:#fff;padding:6px 12px;font-size:1.25em;line-height:1.1;display:block;outline:none;list-style:none;font-weight:bold;}}
summary::-webkit-details-marker {{display: none;}}
summary::after{{content:'\\25C0\\FE0E';float:right;font-size:0.8em;margin-top:2px;}}
details[open] summary::after{{content:'\\25BC\\FE0E';}}
.region-content{{padding:15px;}}
.inner-day{{border-top:1px dashed #000;margin-top:5px;margin-left:-15px;margin-right:-15px;display:block;}}
.inner-day-header{{background:#eee;color:#000;padding:6px 15px;font-size:1.1em;border-bottom:1px solid #ddd;line-height:1.2;margin-bottom:0;display:block;}}
.inner-content{{padding:10px 15px 5px 15px;}}
p{{margin:0 0 10px 0;}}
ul{{margin:8px 0 0 0;padding-left:22px;}}
li{{margin-bottom:6px;}}
.status{{text-align:center;font-size:0.9em;margin-bottom:20px;color:#444;}}
a{{color:inherit;text-decoration:underline;}}
@media screen and (max-width: 600px) {{
  body {{ max-width: 94%; padding: 5px; font-size: 1.1em; }}
  h1 {{ font-size: 1.6em; max-width: 85%; margin: 0 auto 20px auto; }}
  .region-content {{ padding: 10px; }}
  .inner-day {{ margin-left: -10px; margin-right: -10px; }}
  .inner-content {{ padding: 10px 10px 5px 10px; }}
}}
</style></head><body>
<h1>Mountain Dashboard</h1><div class="status">Updated {ts}</div>
{chart}
<details class="region" open><summary>Summary</summary><div class="region-content">
<p>{area_summary}</p>
<div class="inner-day">
  <div class="inner-day-header"><strong>Planning Outlook</strong></div>
  <div class="inner-content"><p>{planning_outlook}</p></div>
</div>
</div></details>
<details class="region"><summary><a href="{urls['mwis_se_highlands']}">SE Highlands</a></summary><div class="region-content">{data['mwis_se_highlands']}</div></details>
<details class="region"><summary><a href="{urls['mwis_cairngorms']}">Cairngorms</a></summary><div class="region-content">{data['mwis_cairngorms']}</div></details>
<details class="region"><summary><a href="{urls['mwis_west']}">W Highlands</a></summary><div class="region-content">{data['mwis_west']}</div></details>
<details class="region"><summary><a href="{urls['mwis_nw_highlands']}">NW Highlands</a></summary><div class="region-content">{data['mwis_nw_highlands']}</div></details>
<details class="region"><summary><a href="https://www.sais.gov.uk/">SAIS Avalanche</a></summary><div class="region-content"><ul>
<li><strong><a href="{urls['sais_s_cairngorms']}">S Cairngorms</a>:</strong> {data['sais_s_cairngorms']}</li>
<li><strong><a href="{urls['sais_n_cairngorms']}">N Cairngorms</a>:</strong> {data['sais_n_cairngorms']}</li>
<li><strong><a href="{urls['sais_glencoe']}">Glencoe</a>:</strong> {data['sais_glencoe']}</li>
<li><strong><a href="{urls['sais_lochaber']}">Lochaber</a>:</strong> {data['sais_lochaber']}</li>
<li><strong><a href="{urls['sais_creag_meagaidh']}">Creag Meagaidh</a>:</strong> {data['sais_creag_meagaidh']}</li>
<li><strong><a href="{urls['sais_torridon']}">Torridon</a>:</strong> {data['sais_torridon']}</li>
</ul></div></details></body></html>"""

with open("index.html", "w", encoding="utf-8") as f: f.write(kindle_tmpl)

# 6. Generate TRMNL HTML (trmnl.html)
trmnl_img = f'<img src="{synoptic_url}" />' if synoptic_url else "<p>No synoptic chart available.</p>"

total_chars = len(area_summary) + len(planning_outlook)
t_body_size = "11pt"
t_header_size = "17px"

if total_chars > 1200:
    t_body_size = "9pt"
    t_header_size = "15px"
elif total_chars > 800:
    t_body_size = "10pt"
    t_header_size = "16px"

trmnl_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{{box-sizing:border-box;}}
body{{margin:0;padding:0;width:800px;height:480px;background:#fff;color:#000;font-family:Georgia,serif;overflow:hidden;display:flex;flex-direction:column;}}
.main-content{{display:flex;width:100%;flex-grow:1;overflow:hidden;}}
.left-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;}}
.left-pane img{{max-width:100%;max-height:100%;object-fit:contain;}}
.right-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;}}
.date-header{{font-size:{t_header_size};font-weight:bold;margin-bottom:5px;display:block;}}
.body-text{{font-size:{t_body_size};line-height:1.2;margin:0 0 15px 0;}}
.outlook-section{{flex-grow:1;overflow:hidden;}}
</style></head><body><div class="main-content">
<div class="left-pane">{trmnl_img}</div>
<div class="right-pane">
    <div class="summary-section">
        <span class="date-header">{trmnl_se_date}</span>
        <p class="body-text">{area_summary}</p>
    </div>
    <div class="outlook-section">
        <p class="body-text">{planning_outlook}</p>
    </div>
</div>
</div></body></html>"""

with open("trmnl.html", "w", encoding="utf-8") as f: f.write(trmnl_tmpl)
