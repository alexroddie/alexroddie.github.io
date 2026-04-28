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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
}

data = {}
planning_outlook = "Planning outlook unavailable."

# Helper to fix MWIS grammar
def format_sentences(lines):
    if not lines: return ""
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if line[-1] not in ".!?": line += "."
        cleaned.append(line)
    return " ".join(cleaned)

# Helper for natural language date/time
def get_natural_timestamp():
    now = datetime.datetime.now()
    day = now.day
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    time_str = now.strftime('%I.%M%p').lower().lstrip('0')
    return now.strftime(f'%A, %B {day}{suffix} at {time_str}')

# Scrape MWIS
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands', 'mwis_nw_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if planning_outlook == "Planning outlook unavailable.":
            capturing_outlook = False
            outlook_lines = []
            for line in lines:
                if "Planning Outlook" in line or "Planning outlook" in line:
                    capturing_outlook = True
                    continue
                if capturing_outlook:
                    if "Issued at" in line or "Forecast issued" in line or "mwis.org.uk" in line.lower(): break
                    if line: outlook_lines.append(line)
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
            if current_day is not None:
                if "Headline for" in line: current_section = "headline"
                elif "How windy?" in line: current_section = "wind"
                elif "How Wet?" in line: current_section = "wet"
                elif "Cloud on the hills?" in line: current_section = "cloud"
                elif "Chance of cloud free" in line: current_section = "chance_cloud_free"
                elif "How Cold?" in line: current_section = "temp"
                elif "Freezing Level" in line: current_section = "freezing_level"
                elif any(x in line for x in ["Summary", "Effect", "Sunshine", "Planning"]): current_section = "ignore"
                
                if current_section == "date_search":
                    day_words = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Today"]
                    for dw in day_words:
                        if dw in line:
                            current_day["date"] = dw
                            current_section = "ignore"
                            break
                elif current_section and current_section != "ignore":
                    current_day[current_section].append(line)
        if current_day: days.append(current_day)
            
        out_html = ""
        for index, day in enumerate(days[:3]): 
            date_label = day.get('date', 'Day')
            headline = format_sentences(day.get('headline', []))
            wind = format_sentences(day.get('wind', []))
            wet = format_sentences(day.get('wet', []))
            cloud = format_sentences(day.get('cloud', []))
            chance_cloud_free = format_sentences(day.get('chance_cloud_free', []))
            temp = format_sentences(day.get('temp', []))
            freezing_level = format_sentences(day.get('freezing_level', []))
            
            day_content = f"<p style='margin-top:0; margin-bottom:5px;'><em>{headline.rstrip('.')}</em>.</p>"
            day_content += "<ul style='margin-top: 5px; margin-bottom: 10px; padding-left: 20px;'>"
            if wind: day_content += f"<li><strong>Wind:</strong> {wind}</li>"
            if wet: day_content += f"<li><strong>Wet:</strong> {wet}</li>"
            if cloud: day_content += f"<li><strong>Cloud:</strong> {cloud}</li>"
            if chance_cloud_free: day_content += f"<li><strong>Cloud-free:</strong> {chance_cloud_free}</li>"
            if temp: day_content += f"<li><strong>Temp:</strong> {temp}</li>"
            if freezing_level: day_content += f"<li><strong>Freezing:</strong> {freezing_level}</li>"
            day_content += "</ul>"

            if index > 0:
                out_html += f"<details class='inner-day'><summary><strong>{date_label}</strong></summary><div class='inner-content'>{day_content}</div></details>"
            else:
                out_html += f"<div class='day-one'><strong>{date_label}:</strong> {day_content}</div>"
            
        data[key] = out_html
    except Exception as e:
        data[key] = f"Error: {str(e)}"

# Scrape SAIS
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        text_content = soup.get_text(separator='\n').lower()
        if "finished for the winter" in text_content: data[key] = "Reporting finished for the winter season."
        else:
            hazard = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = hazard.text.strip() if hazard else "Hazard not found."
    except Exception as e: data[key] = f"Error: {str(e)}"

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mountain Weather Dashboard</title>
<style>
  body {{ font-family: Georgia, serif; background: #fff; color: #000; margin: 0; padding: 10px; line-height: 1.4; }}
  h1 {{ font-size: 1.8em; border-bottom: 3px solid #000; padding-bottom: 5px; margin-top: 0; text-align: center; }}
  .region, details.region {{ border: 2px solid #000; margin-bottom: 15px; padding: 0; }}
  div.region h2 {{ background: #000; }}
  summary {{ list-style: none; cursor: pointer; outline: none; background: #000; display: block; }}
  summary::-webkit-details-marker {{ display: none; }}
  h2 {{ font-size: 1.3em; margin: 0; color: #fff; padding: 5px 10px; }}
  summary h2::after {{ content: '◀'; float: right; font-size: 0.8em; margin-top: 2px; }}
  details[open] summary h2::after {{ content: '▼'; }}
  
  details.inner-day {{ border-top: 1px dashed #000; margin-top: 10px; }}
  details.inner-day summary {{ background: #eee; color: #000; padding: 5px 10px; font-size: 1.1em; }}
  details.inner-day summary::after {{ content: '◀'; float: right; }}
  details.inner-day[open] summary::after {{ content: '▼'; }}
  .inner-content {{ padding: 10px 0 0 0; }}
  .day-one {{ margin-bottom: 10px; }}

  a {{ color: #000; text-decoration: underline; }}
  h2 a {{ color: #fff; text-decoration: underline; text-decoration-style: dotted; }}
  .status {{ text-align: center; font-size: 0.9em; font-style: italic; margin-bottom: 15px; }}
  .region-content {{ padding: 10px; }}
  ul {{ margin-top: 5px; padding-left: 20px; }}
  li {{ margin-bottom: 4px; font-size: 1.05em; }}
</style>
</head>
<body>
  <h1>Mountain Weather Dashboard</h1>
  <div class="status">Updated {get_natural_timestamp()}</div>

  <div class="region">
    <h2>Planning Outlook (All Areas)</h2>
    <div class="region-content"><p>{planning_outlook}</p></div>
  </div>

  <details class="region">
    <summary><h2><a href="{urls['mwis_se_highlands']}">SE Highlands</a></h2></summary>
    <div class="region-content">{data['mwis_se_highlands']}</div>
  </details>
  <details class="region">
    <summary><h2><a href="{urls['mwis_cairngorms']}">Cairngorms</a></h2></summary>
    <div class="region-content">{data['mwis_cairngorms']}</div>
  </details>
  <details class="region">
    <summary><h2><a href="{urls['mwis_west']}">W Highlands</a></h2></summary>
    <div class="region-content">{data['mwis_west']}</div>
  </details>
  <details class="region">
    <summary><h2><a href="{urls['mwis_nw_highlands']}">NW Highlands</a></h2></summary>
    <div class="region-content">{data['mwis_nw_highlands']}</div>
  </details>

  <details class="region">
    <summary><h2>SAIS Avalanche Conditions</h2></summary>
    <div class="region-content">
      <ul>
          <li><strong><a href="{urls['sais_n_cairngorms']}">Northern Cairngorms</a>:</strong> {data['sais_n_cairngorms']}</li>
          <li><strong><a href="{urls['sais_s_cairngorms']}">Southern Cairngorms</a>:</strong> {data['sais_s_cairngorms']}</li>
          <li><strong><a href="{urls['sais_lochaber']}">Lochaber</a>:</strong> {data['sais_lochaber']}</li>
          <li><strong><a href="{urls['sais_glencoe']}">Glencoe</a>:</strong> {data['sais_glencoe']}</li>
      </ul>
    </div>
  </details>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
