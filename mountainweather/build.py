import requests
from bs4 import BeautifulSoup
import datetime

urls = {
    'mwis_west': 'https://www.mwis.org.uk/forecasts/scottish/west-highlands/text',
    'mwis_cairngorms': 'https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text',
    'mwis_se_highlands': 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text',
    'sais_n_cairngorms': 'https://www.sais.gov.uk/northern-cairngorms/',
    'sais_s_cairngorms': 'https://www.sais.gov.uk/southern-cairngorms/',
    'sais_lochaber': 'https://www.sais.gov.uk/lochaber/',
    'sais_glencoe': 'https://www.sais.gov.uk/glencoe/'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
}

data = {}

# Scrape MWIS
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Grab all text and split into a clean list of lines
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        days = []
        current_day = None
        current_section = None
        
        for line in lines:
            # Trigger a new day block
            if "Viewing Forecast For" in line:
                if current_day:
                    days.append(current_day)
                current_day = {
                    "date": "Today", "headline": [], "wind": [], "wet": [], 
                    "cloud": [], "chance_cloud_free": [], "temp": [], "freezing_level": []
                }
                current_section = "date_search"
                continue
                
            if current_day is not None:
                # Check for specific data headings
                if "Headline for" in line:
                    current_section = "headline"
                    continue
                elif "How windy?" in line:
                    current_section = "wind"
                    continue
                elif "How Wet?" in line:
                    current_section = "wet"
                    continue
                elif "Cloud on the hills?" in line:
                    current_section = "cloud"
                    continue
                elif "Chance of cloud free" in line:
                    current_section = "chance_cloud_free"
                    continue
                elif "How Cold?" in line:
                    current_section = "temp"
                    continue
                elif "Freezing Level" in line:
                    current_section = "freezing_level"
                    continue
                # Ignore sections we don't want cluttering the screen
                elif any(ignore_str in line for ignore_str in ["Summary for all mountain areas", "Effect of the wind", "Sunshine and air", "Planning Outlook"]):
                    current_section = "ignore"
                    continue
                
                # Append the text to the correct category
                if current_section == "date_search":
                    # Hunt for the day of the week to label the forecast
                    day_words = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Today"]
                    for dw in day_words:
                        if dw in line:
                            current_day["date"] = dw
                            current_section = "ignore"
                            break
                elif current_section and current_section != "ignore":
                    current_day[current_section].append(line)
                    
        if current_day:
            days.append(current_day)
            
        # Format the extracted data into a headline and a bulleted list
        out_html = ""
        for day in days[:2]: # Only process Day 1 and Day 2 (Today/Tomorrow)
            date_label = day.get('date', 'Day')
            headline = " ".join(day.get('headline', []))
            wind = " ".join(day.get('wind', []))
            wet = " ".join(day.get('wet', []))
            cloud = " ".join(day.get('cloud', []))
            chance_cloud_free = " ".join(day.get('chance_cloud_free', []))
            temp = " ".join(day.get('temp', []))
            freezing_level = " ".join(day.get('freezing_level', []))
            
            para = f"<strong>{date_label}:</strong>"
            if headline:
                para += f" <em>{headline}.</em>"
            
            out_html += f"<p style='margin-top:0; margin-bottom:5px; font-size:1.05em;'>{para}</p>"
            
            # Build the bulleted list if there is data
            if wind or wet or cloud or temp or chance_cloud_free or freezing_level:
                out_html += "<ul style='margin-top: 5px; margin-bottom: 15px; padding-left: 20px; font-size: 1.05em;'>"
                if wind: out_html += f"<li style='margin-bottom: 4px;'><strong>Wind:</strong> {wind}</li>"
                if wet: out_html += f"<li style='margin-bottom: 4px;'><strong>Wet:</strong> {wet}</li>"
                if cloud: out_html += f"<li style='margin-bottom: 4px;'><strong>Cloud:</strong> {cloud}</li>"
                if chance_cloud_free: out_html += f"<li style='margin-bottom: 4px;'><strong>Cloud-free Munros:</strong> {chance_cloud_free}</li>"
                if temp: out_html += f"<li style='margin-bottom: 4px;'><strong>Temp:</strong> {temp}</li>"
                if freezing_level: out_html += f"<li style='margin-bottom: 4px;'><strong>Freezing Level:</strong> {freezing_level}</li>"
                out_html += "</ul>"
            
        data[key] = out_html if out_html else "<div>Forecast data could not be parsed.</div>"
            
    except Exception as e:
        data[key] = f"Error fetching forecast: {str(e)}"

# Scrape SAIS
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        text_content = soup.get_text(separator='\n').lower()
        
        if "finished for the winter" in text_content:
            data[key] = "Reporting finished for the winter season."
        else:
            hazard = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = hazard.text.strip() if hazard else "Live hazard data not found."
    except Exception as e:
         data[key] = f"Report unavailable. Error: {str(e)}"

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
  h2 {{ font-size: 1.3em; margin: 0 0 10px 0; background: #000; color: #fff; padding: 5px 10px; }}
  
  /* Link styling optimized for e-ink contrast */
  a {{ color: #000; text-decoration: underline; }}
  h2 a {{ color: #fff; text-decoration: underline; text-decoration-style: dotted; }}
  
  p {{ margin: 5px 0; font-size: 1.1em; }}
  .status {{ text-align: center; font-size: 0.8em; font-style: italic; margin-bottom: 15px; font-weight: bold; }}
  .region {{ border: 2px solid #000; margin-bottom: 15px; padding: 0; }}
  .region-content {{ padding: 10px; }}
</style>
</head>
<body>
  <h1>Mountain Weather Dashboard</h1>
  <div class="status">Last automatically updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>

  <div class="region">
    <h2><a href="{urls['mwis_se_highlands']}">Southeastern Highlands (MWIS)</a></h2>
    <div class="region-content">{data['mwis_se_highlands']}</div>
  </div>
  
  <div class="region">
    <h2><a href="{urls['mwis_cairngorms']}">Cairngorms & Monadhliath (MWIS)</a></h2>
    <div class="region-content">{data['mwis_cairngorms']}</div>
  </div>
  
  <div class="region">
    <h2><a href="{urls['mwis_west']}">West Highlands (MWIS)</a></h2>
    <div class="region-content">{data['mwis_west']}</div>
  </div>

  <div class="region">
    <h2>SAIS Avalanche Conditions</h2>
    <div class="region-content">
      <ul style='margin-top: 5px; margin-bottom: 15px; padding-left: 20px; font-size: 1.05em;'>
          <li style='margin-bottom: 4px;'><strong><a href="{urls['sais_n_cairngorms']}">Northern Cairngorms</a>:</strong> {data['sais_n_cairngorms']}</li>
          <li style='margin-bottom: 4px;'><strong><a href="{urls['sais_s_cairngorms']}">Southern Cairngorms</a>:</strong> {data['sais_s_cairngorms']}</li>
          <li style='margin-bottom: 4px;'><strong><a href="{urls['sais_lochaber']}">Lochaber</a>:</strong> {data['sais_lochaber']}</li>
          <li style='margin-bottom: 4px;'><strong><a href="{urls['sais_glencoe']}">Glencoe</a>:</strong> {data['sais_glencoe']}</li>
      </ul>
    </div>
  </div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
