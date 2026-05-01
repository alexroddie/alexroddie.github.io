import requests
from bs4 import BeautifulSoup

# 1. Configuration
mwis_text_url = 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text'
synoptic_url = 'https://www.mwis.org.uk/forecasts/synoptic-charts'
headers = {'User-Agent': 'Mozilla/5.0'}

# 2. Fetch Synoptic Chart
chart_src = None
try:
    res = requests.get(synoptic_url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if ('chart' in src.lower() or 'synoptic' in src.lower()) and 'logo' not in src.lower():
            chart_src = "https://www.mwis.org.uk" + src if src.startswith('/') else src
            break
except:
    pass

# 3. Fetch and Parse Text Data
area_summary = "Summary unavailable."
planning_outlook = "Outlook unavailable."
trmnl_se_date = "Today"

try:
    res = requests.get(mwis_text_url, headers=headers, timeout=10)
    # Get raw text, separating visual blocks with newlines
    raw_text = BeautifulSoup(res.text, 'html.parser').get_text(separator='\n')
    
    # Clean up empty lines and strip whitespace
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Extract Summary: Find "Summary", grab the line immediately after it.
    for i, line in enumerate(lines):
        if "summary" in line.lower() and i + 1 < len(lines):
            # Ensure we don't accidentally grab a different header
            if len(lines[i+1]) > 20: 
                area_summary = lines[i+1]
            break

    # Extract Outlook: It is always the very last line of the document
    if lines:
        planning_outlook = lines[-1]

    # Extract Date: Grab the first "Day" block and aggressively strip "Forecast"
    for line in lines:
        if any(day in line for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            if len(line) < 40 and not any(word in line.lower() for word in ["summary", "outlook", "wind", "cloud"]):
                # Forcefully remove "Forecast" or "'s Forecast" to leave just the day/date
                trmnl_se_date = line.replace("'s Forecast", "").replace(" Forecast", "").strip()
                break
                
except Exception as e:
    area_summary = f"Error fetching text data: {e}"
    planning_outlook = "Check connection."

# 4. Generate TRMNL Layout with Tweaked Scaling
trmnl_img = f'<img src="{chart_src}" />' if chart_src else "<p>No synoptic chart available.</p>"

total_chars = len(area_summary) + len(planning_outlook)

# Default base sizing
t_body_size = "11pt"
t_header_size = "17pt"

# Adjusted scaling rules
if total_chars > 1200:
    t_body_size = "9pt"
    t_header_size = "15pt"
elif total_chars > 800:
    t_body_size = "10pt"
    t_header_size = "16pt"
elif total_chars < 600:
    t_body_size = "12pt"
    t_header_size = "18pt"

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
        <p class="body-text"><strong>Summary:</strong> {area_summary}</p>
    </div>
    <div class="outlook-section">
        <p class="body-text"><strong>Outlook:</strong> {planning_outlook}</p>
    </div>
</div>
</div></body></html>"""

with open("trmnl.html", "w", encoding="utf-8") as f:
    f.write(trmnl_tmpl)
