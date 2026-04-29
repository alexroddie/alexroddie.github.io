import requests, datetime
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
trmnl_se_date, trmnl_se_headline = "", ""

def format_text(lines):
    ignore = ["how windy?", "how wet?", "cloud on the hills?", "how cold?", "freezing level", "headline for", "chance of cloud free"]
    cleaned = []
    for l in [line.strip() for line in lines if line.strip()]:
        if not any(p in l.lower() for p in ignore):
            cleaned.append(l if l[-1] in ".!?" else l + ".")
    return " ".join(cleaned)

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
        lines = [l.strip() for l in soup.get_text(separator='\n').split('\n') if l.strip()]
        
        if area_summary == "Summary unavailable.":
            sum_l, sum_cap = [], False
            for l in lines:
                if "summary for all mountain areas" in l.lower(): sum_cap = True; continue
                if sum_cap:
                    if any(x in l.lower() for x in ["headline for", "issued at", "forecast issued", "mwis.org.uk", "planning outlook"]): sum_cap = False; break
                    sum_l.append(l)
            if sum_l: area_summary = format_text(sum_l)

        if planning_outlook == "Outlook unavailable.":
            out_l, cap = [], False
            for l in lines:
                if "planning outlook" in l.lower(): cap = True; continue
                if cap:
                    if any(x in l.lower() for x in ["issued at", "forecast issued", "mwis.org.uk"]): cap = False; continue
                    out_l.append(l)
            if out_l: planning_outlook = format_text(out_l)

        days, cur = [], None
        for l in lines:
            if "Viewing Forecast For" in l:
                if cur: days.append(cur)
                cur = {"date": "Today", "headline":[], "wind":[], "wet":[], "cloud":[], "chance_cloud_free":[], "temp":[], "freezing_level":[]}
                sec = "date"
                continue
            if cur:
                if "Headline for" in l: sec = "headline"
                elif "How windy?" in l: sec = "wind"
                elif "How Wet?" in l: sec = "wet"
                elif "Cloud on the hills?" in l: sec = "cloud"
                elif "Chance of cloud free" in l: sec = "chance_cloud_free"
                elif "How Cold?" in l: sec = "temp"
                elif "Freezing Level" in l: sec = "freezing_level"
                elif any(x in l for x in ["Summary", "Effect", "Sunshine", "Planning"]): sec = "ignore"
                elif sec == "date":
                    for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
                        if d in l: cur["date"] = d; sec = "ignore"; break
                elif sec != "ignore": cur[sec].append(l)
        if cur: days.append(cur)
        
        if key == 'mwis_se_highlands' and len(days) > 0:
            trmnl_se_date = days[0].get('date', 'Today')
            trmnl_se_headline = format_text(days[0].get('headline', []))
        
        html = ""
        for i, d in enumerate(days[:3]):
            head = format_text(d['headline'])
            content = f"<p><em>{head.rstrip('.')}</em>.</p>" if head else ""
            content += "<ul>"
            for lbl, fld in [("Wind","wind"),("Wet","wet"),("Cloud","cloud"),("Chance of cloud-free Munros","chance_cloud_free"),("Temp","temp"),("Freezing level","freezing_level")]:
                val = format_text(d[fld])
                if val: content += f"<li><strong>{lbl}:</strong> {val}</li>"
            content += "</ul>"
            if i > 0: html += f"<div class='inner-day'><div class='inner-day-header'><strong>{d['date']}</strong></div><div class='inner-content'>{content}</div></div>"
            else: html += f"<div class='day-one'><strong>{d['date']}</strong>{content}</div>"
        data[key] = html
    except: data[key] = "Error fetching region."

# 3. Scrape SAIS
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe', 'sais_creag_meagaidh', 'sais_torridon']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        if "finished" in soup.get_text().lower(): data[key] = "Season finished."
        else:
            h = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = h.text.strip() if h else "No data."
    except: data[key] = "Error."

# 4. Generate Timestamps & Chart HTML
now = datetime.datetime.now(ZoneInfo("Europe/London"))
suff = 'th' if 11<=now.day<=13 else {1:'st',2:'nd',3:'rd'}.get(now.day%10, 'th')
time_str = now.strftime('%I.%M%p').lower().lstrip('0')
ts = now.strftime(f'%A, %B {now.day}{suff} at {time_str}')

# Added class="chart-container" for mobile targeting
chart = f'<div class="chart-container" style="text-align:center;margin-bottom:20px;"><a href="{urls["mwis_synoptic"]}"><img src="{synoptic_url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"/></a></div>' if synoptic_url else ""

# 5. Generate Kindle HTML (index.html)
kindle_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{{font-family:Georgia,serif;padding:10px;line-height:1.5;background:#fff;color:#000;max-width:94%;margin:0 auto;}}
h1{{text-align:center;border-bottom:3px solid #000;padding-bottom:10px;margin-bottom:20px;line-height:1.1;}}
.region,details.region{{border:2px solid #000;margin-bottom:20px;padding:0;}}
h2{{background:#000;color:#fff;padding:6px 12px;margin:0!important;font-size:1.25em;line-height:1.1;display:block;}}
summary{{cursor:pointer;background:#000;display:block;outline:none;}}
summary h2::after{{content:'\\25C0\\FE0E';float:right;font-size:0.8em;margin-top:2px;}}
details[open] summary h2::after{{content:'\\25BC\\FE0E';}}
.region-content{{padding:15px;}}
.inner-day{{border-top:1px dashed #000;margin-top:5px;margin-left:-15px;margin-right:-15px;display:block;}}
.inner-day-header{{background:#eee;color:#000;padding:6px 15px;font-size:1.1em;border-bottom:1px solid #ddd;line-height:1.2;margin-bottom:0;display:block;}}
.inner-content{{padding:10px 15px 5px 15px;}}
p{{margin:0 0 10px 0;}}
ul{{margin:8px 0 0 0;padding-left:22px;}}
li{{margin-bottom:6px;}}
.status{{text-align:center;font-size:0.9em;margin-bottom:20px;color:#444;}}
a{{color:inherit;text-decoration:underline;}}

/* Mobile responsiveness logic */
@media screen and (max-width: 600px) {{
  body {{ max-width: 98%; padding: 5px; font-size: 1.1em; }}
  /* Scaled down heading size and narrowed width */
  h1 {{ font-size: 1.6em; max-width: 85%; margin: 0 auto 20px auto; }}
  .region-content {{ padding: 10px; }}
  .inner-day {{ margin-left: -10px; margin-right: -10px; }}
  .inner-content {{ padding: 10px 10px 5px 10px; }}
  /* Force chart image to match box width */
  .chart-container a img {{ width: 100%; }}
}}
</style></head><body>
<h1>Mountain Dashboard</h1><div class="status">Updated {ts}</div>
{chart}
<div class="region"><h2>Summary</h2><div class="region-content">
<p>{area_summary}</p>
<div class="inner-day">
  <div class="inner-day-header"><strong>Planning Outlook</strong></div>
  <div class="inner-content"><p>{planning_outlook}</p></div>
</div>
</div></div>
<details class="region"><summary><h2><a href="{urls['mwis_se_highlands']}">SE Highlands</a></h2></summary><div class="region-content">{data['mwis_se_highlands']}</div></details>
<details class="region"><summary><h2><a href="{urls['mwis_cairngorms']}">Cairngorms</a></h2></summary><div class="region-content">{data['mwis_cairngorms']}</div></details>
<details class="region"><summary><h2><a href="{urls['mwis_west']}">W Highlands</a></h2></summary><div class="region-content">{data['mwis_west']}</div></details>
<details class="region"><summary><h2><a href="{urls['mwis_nw_highlands']}">NW Highlands</a></h2></summary><div class="region-content">{data['mwis_nw_highlands']}</div></details>
<details class="region"><summary><h2><a href="https://www.sais.gov.uk/">SAIS Avalanche</a></h2></summary><div class="region-content"><ul>
<li><strong><a href="{urls['sais_s_cairngorms']}">S Cairngorms</a>:</strong> {data['sais_s_cairngorms']}</li>
<li><strong><a href="{urls['sais_n_cairngorms']}">N Cairngorms</a>:</strong> {data['sais_n_cairngorms']}</li>
<li><strong><a href="{urls['sais_glencoe']}">Glencoe</a>:</strong> {data['sais_glencoe']}</li>
<li><strong><a href="{urls['sais_lochaber']}">Lochaber</a>:</strong> {data['sais_lochaber']}</li>
<li><strong><a href="{urls['sais_creag_meagaidh']}">Creag Meagaidh</a>:</strong> {data['sais_creag_meagaidh']}</li>
<li><strong><a href="{urls['sais_torridon']}">Torridon</a>:</strong> {data['sais_torridon']}</li>
</ul></div></details></body></html>"""

with open("index.html", "w", encoding="utf-8") as f: f.write(kindle_tmpl)

# 6. Generate TRMNL HTML (trmnl.html)
trmnl_img = f'<img src="{synoptic_url}" />' if synoptic_url else "<p>No synoptic chart available today.</p>"
se_summary_html = f"<div style='margin-bottom: 15px;'><strong style='font-size: 16px;'>{trmnl_se_date}</strong><p style='margin: 5px 0 0 0;'>{trmnl_se_headline.rstrip('.')}.</p></div>" if trmnl_se_date else ""
trmnl_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{{box-sizing:border-box;}}
body{{margin:0;padding:0;width:800px;height:480px;background:#fff;color:#000;font-family:Georgia,serif;overflow:hidden;display:flex;flex-direction:column;}}
.main-content{{display:flex;width:100%;flex-grow:1;overflow:hidden;}}
.left-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;}}
.left-pane img{{max-width:100%;max-height:100%;object-fit:contain;}}
.right-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;}}
.outlook-content{{font-size:10pt;line-height:1.4;overflow:hidden;flex-grow:1;}}
.outlook-content p{{margin-top:0;}}.right-pane em,.outlook-content em{{font-style:normal;}}
</style></head><body><div class="main-content"><div class="left-pane">{trmnl_img}</div><div class="right-pane">{se_summary_html}<div class="outlook-content"><p>{planning_outlook}</p></div></div></div></body></html>"""

with open("trmnl.html", "w", encoding="utf-8") as f: f.write(trmnl_tmpl)
