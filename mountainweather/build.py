import requests
from bs4 import BeautifulSoup
import datetime

urls = {
    'mwis_west': 'https://www.mwis.org.uk/forecasts/scottish/west-highlands/text',
    'mwis_cairngorms': 'https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text',
    'mwis_se_highlands': 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text',
    'mwis_nw_highlands': 'https://www.mwis.org.uk/forecasts/scottish/the-northwest-highlands/text',
    'sais_n_cairngorms': 'https://www.sais.gov.uk/northern-cairngorms/',
    'sais_s_cairngorms': 'https://www.sais.gov.uk/southern-cairngorms/',
    'sais_lochaber': 'https://www.sais.gov.uk/lochaber/',
    'sais_glencoe': 'https://www.sais.gov.uk/glencoe/'
}

headers = {'User-Agent': 'Mozilla/5.0'}
data = {}
planning_outlook = "Planning outlook unavailable."

def format_sentences(lines):
    if not lines: return ""
    cleaned = []
    ignore = ["how windy?", "how wet?", "cloud on the hills?", "how cold?", "freezing level", "headline for", "chance of cloud free"]
    for line in lines:
        line = line.strip()
        if not line or any(p in line.lower() for p in ignore): continue
        if line[-1] not in ".!?": line += "."
        cleaned.append(line)
    return " ".join(cleaned)

def get_natural_timestamp():
    now = datetime.datetime.now()
    day = now.day
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    time_str = now.strftime('%I.%M%p').lower().lstrip('0')
    return now.strftime(f'%A, %B {day}{suffix} at {time_str}')


for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands', 'mwis_nw_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        lines = [line.strip() for line in soup.get_text(separator='\n').split('\n') if line.strip()]
        
        if planning_outlook == "Planning outlook unavailable.":
            capturing = False
            outlook_lines = []
            for line in lines:
                if "planning outlook" in line.lower(): capturing = True; continue
                if capturing:
                    if any(x in line.lower() for x in ["issued at", "forecast issued", "mwis.org.uk"]): break
                    outlook_lines.append(line)
            if outlook_lines: planning_outlook = format_sentences(outlook_lines)

        days = []
        current_day = None
        current_section = None
        for line in lines:
            if "Viewing Forecast For" in line:
                if current_day: days.append(current_day)
                current_day = {"date": "Today", "headline": [], "wind": [], "wet": [], "cloud": [], "chance_cloud_free": [], "temp": [], "freezing_level": []}
                current_section = "date_search"
                continue
            if current_day:
                if "Headline for" in line: current_section = "headline"; continue
                elif "How windy?" in line: current_section = "wind"; continue
                elif "How Wet?" in line: current_section = "wet"; continue
                elif "Cloud on the hills?" in line: current_section = "cloud"; continue
                elif "Chance of cloud free" in line: current_section = "chance_cloud_free"; continue
                elif "How Cold?" in line: current_section = "temp"; continue
                elif "Freezing Level" in line: current_section = "freezing_level"; continue
                elif any(x in line for x in ["Summary", "Effect", "Sunshine", "Planning"]): current_section = "ignore"; continue
                if current_section == "date_search":
                    for dw in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Today"]:
                        if dw in line: current_day["date"] = dw; current_section = "ignore"; break
                elif current_section != "ignore": current_day[current_section].append(line)
        if current_day: days.append(current_day)
            
        out_html = ""
        for i, day in enumerate(days[:3]): 
            date_label = day.get('date', 'Day')
            headline = format_sentences(day.get('headline', []))
            content = ""
            if headline:
                content += f"<p style='margin-top:0; margin-bottom:8px;'><em>{headline.rstrip('.')}</em>.</p>"
            content += "<ul>"
            for label, field in [("Wind", "wind"), ("Wet", "wet"), ("Cloud", "cloud"), ("Chance of cloud-free Munros", "chance_cloud_free"), ("Temp", "temp"), ("Freezing level", "freezing_level")]:
                val = format_sentences(day.get(field, []))
                if val: content += f"<li><strong>{label}:</strong> {val}</li>"
            content += "</ul>"
            
            if i > 0: 
                out_html += f"<div class='inner-day'><div class='inner-day-header'><strong>{date_label}</strong></div><div class='inner-content'>{content}</div></div>"
            else: 
                out_html += f"<div class='day-one'><strong>{date_label}</strong>{content}</div>"
        data[key] = out_html
    except Exception as e: data[key] = f"Error: {str(e)}"


for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        if "finished for the winter" in soup.get_text().lower(): data[key] = "Season finished."
        else:
            h = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = h.text.strip() if h else "Hazard data not found."
    except: data[key] = "Error fetching SAIS."

html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  body {{ font-family: Georgia, serif; padding: 10px; line-height: 1.5; background: #fff; color: #000; }}
  h1 {{ text-align: center; border-bottom: 3px solid #000; padding-bottom: 10px; margin-bottom: 20px; line-height: 1.2; }}
  
  .region, details.region {{ border: 2px solid #000; margin-bottom: 20px; padding: 0; }}
  
  /* CRITICAL: Constrain header height for Kindle */
  h2 {{ 
    background: #000; 
    color: #fff; 
    padding: 6px 12px; 
    margin: 0 !important; 
    font-size: 1.25em; 
    line-height: 1.1; 
    display: block;
  }}
  
  summary {{ cursor: pointer; background: #000; display: block; outline: none; margin: 0; padding: 0; }}
  summary h2::after {{ content: '\\25C0\\FE0E'; float: right; font-size: 0.8em; margin-top: 2px; }}
  details[open] summary h2::after {{ content: '\\25BC\\FE0E'; }}
  
  .region-content {{ padding: 15px; }}
  .inner-content {{ padding: 12px 15px; }}
  .day-one {{ margin-bottom: 15px; }}
  
  .inner-day {{ border-top: 1px dashed #000; margin-top: 15px; margin-left: -15px; margin-right: -15px; }}
  .inner-day-header {{ background: #eee; color: #000; padding: 6px 15px; font-size: 1.1em; border-bottom: 1px solid #ddd; line-height: 1.2; }}

  p {{ margin: 0 0 10px 0; }}
  ul {{ margin: 8px 0; padding-left: 22px; }}
  li {{ margin-bottom: 6px; }}
  
  .status {{ text-align: center; font-style: italic; font-size: 0.9em; margin-bottom: 20px; color: #444; }}
  a {{ color: inherit; text-decoration: underline; }}
</style></head><body>
  <h1>Mountain Dashboard</h1>
  <div class="status">Updated {get_natural_timestamp()}</div>
  
  <div class="region">
    <h2>Planning Outlook</h2>
    <div class="region-content"><p>{planning_outlook}</p></div>
  </div>
  
  <details class="region"><summary><h2><a href="{urls['mwis_se_highlands']}">SE Highlands</a></h2></summary><div class="region-content">{data['mwis_se_highlands']}</div></details>
  <details class="region"><summary><h2><a href="{urls['mwis_cairngorms']}">Cairngorms</a></h2></summary><div class="region-content">{data['mwis_cairngorms']}</div></details>
  <details class="region"><summary><h2><a href="{urls['mwis_west']}">W Highlands</a></h2></summary><div class="region-content">{data['mwis_west']}</div></details>
  <details class="region"><summary><h2><a href="{urls['mwis_nw_highlands']}">NW Highlands</a></h2></summary><div class="region-content">{data['mwis_nw_highlands']}</div></details>
  
  <details class="region"><summary><h2>SAIS Avalanche</h2></summary><div class="region-content"><ul>
    <li><strong>N Cairngorms:</strong> {data['sais_n_cairngorms']}</li>
    <li><strong>S Cairngorms:</strong> {data['sais_s_cairngorms']}</li>
    <li><strong>Lochaber:</strong> {data['sais_lochaber']}</li>
    <li><strong>Glencoe:</strong> {data['sais_glencoe']}</li>
  </ul></div></details>
</body></html>"""

with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
