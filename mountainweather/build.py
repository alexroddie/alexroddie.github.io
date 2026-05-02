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
    raw_text = BeautifulSoup(res.text, 'html.parser').get_text(separator='\n')
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Extract Summary
    for i, line in enumerate(lines):
        if "summary" in line.lower() and i + 1 < len(lines):
            area_summary = lines[i+1]
            break

    # Extract Outlook
    for i, line in enumerate(lines):
        if ("planning outlook" in line.lower() or "looking ahead" in line.lower()) and i + 1 < len(lines):
            planning_outlook = lines[i+1]
            break

    # Extract Date
    found_viewing_marker = False
    for line in lines:
        if "viewing forecast for" in line.lower():
            found_viewing_marker = True
            
        if found_viewing_marker and any(day in line for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            trmnl_se_date = line.strip()
            break
            
    # Fallback Date
    if trmnl_se_date == "Today":
        for line in lines:
             if any(day in line for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                 if len(line) < 40 and not any(word in line.lower() for word in ["summary", "outlook", "wind", "cloud"]):
                     trmnl_se_date = line.strip()
                     break

except Exception as e:
    area_summary = f"Error fetching text data: {e}"
    planning_outlook = "Check connection."

# 4. Generate Layout (TRMNL Default + Kindle Media Query)
trmnl_img = f'<a href="{synoptic_url}"><img src="{chart_src}" /></a>' if chart_src else "<p>No synoptic chart available.</p>"

total_chars = len(area_summary) + len(planning_outlook)

# Default base sizing (under 680 chars) for TRMNL
t_body_size = "12pt"
t_header_size = "17pt"

# Cascading adjustments based on character thresholds for TRMNL
if total_chars > 1200:
    t_body_size = "9pt"
    t_header_size = "15pt"
elif total_chars > 830:
    t_body_size = "10pt"
    t_header_size = "16pt"
elif total_chars > 680:
    t_body_size = "11pt"
    t_header_size = "16pt"

trmnl_tmpl = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{{box-sizing:border-box;}}

/* TRMNL STRICT DEFAULTS (800x480) - Uses dynamic scaling */
body{{
    margin:0; padding:0;
    width:800px; height:480px; 
    background:#fff; color:#000; 
    font-family:Georgia,serif;
    overflow:hidden; 
    display:flex; flex-direction:column;
}}
.main-content{{display:flex;width:100%;flex-grow:1;flex-direction:row;}}
.left-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;}}
.left-pane img{{max-width:100%;max-height:100%;object-fit:contain;}}
.right-pane{{width:50%;height:100%;padding:25px;display:flex;flex-direction:column;}}
.date-header{{font-size:{t_header_size};font-weight:bold;margin-bottom:5px;display:block;}}
.body-text{{font-size:{t_body_size};line-height:1.2;margin:0 0 15px 0;}}
.outlook-section{{flex-grow:1;overflow:hidden;}}

/* HIDDEN BY DEFAULT FOR TRMNL */
.mobile-links {{ display: none; }}

/* KINDLE / MOBILE ESCAPE HATCH (Triggered under 799px width or portrait mode) */
@media screen and (max-width: 799px), screen and (orientation: portrait) {{
    body {{ 
        width: auto; height: auto; min-height: 100vh;
        overflow: auto; 
    }}
    .main-content {{ flex-direction: column; width: 95%; margin: 0 auto; }}
    .left-pane {{ width: 100%; height: auto; padding: 15px 15px 5px 15px; }}
    .right-pane {{ width: 100%; height: auto; padding: 5px 15px 15px 15px; }}
    .outlook-section {{ overflow: visible; }}
    
    /* OVERRIDE DYNAMIC SCALING - Lock to static reading sizes for mobile */
    .date-header {{ font-size: 20pt; }}
    .body-text {{ font-size: 16pt; }}
    
    /* REVEAL MOBILE LINKS */
    .mobile-links {{
        display: block;
        margin-top: 16px;
        font-size: 16pt; /* Static size to match body text */
    }}
    
    /* FORCE CLEAN BLACK LINKS */
    .mobile-links a {{ color: #000; }}
    
    /* FORCE CLEAN BLACK ARROWS (Hides default browser arrow, injects text-only chevron) */
    .mobile-links summary {{ 
        cursor: pointer; 
        font-weight: bold; 
        margin-bottom: 8px; 
        list-style: none; 
    }}
    .mobile-links summary::-webkit-details-marker {{ display: none; }}
    .mobile-links summary::before {{
        content: '\\25B6\\FE0E'; /* Right-pointing triangle + text-presentation modifier */
        display: inline-block;
        margin-right: 8px;
        color: #000;
    }}
    .mobile-links details[open] summary::before {{
        content: '\\25BC\\FE0E'; /* Down-pointing triangle + text-presentation modifier */
    }}
    
    /* INCREASED INDENTATION FOR LIST ITEMS */
    .mobile-links ul {{ margin: 0; padding-left: 32px; }}
    .mobile-links li {{ margin-bottom: 8px; }}
    .mobile-links details {{ margin-bottom: 12px; }}
}}
</style></head><body><div class="main-content">
<div class="left-pane">{trmnl_img}</div>
<div class="right-pane">
    <div class="summary-section">
        <span class="date-header">{trmnl_se_date}</span>
        <p class="body-text"><strong>Summary:</strong> {area_summary}</p>
    </div>
    <div class="outlook-section">
        <p class="body-text"><strong>Outlook:</strong> {planning_outlook}</p>
        
        <div class="mobile-links">
            <details open>
                <summary>MWIS forecasts</summary>
                <ul>
                    <li><a href="https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text">SE Highlands</a></li>
                    <li><a href="https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text">Cairngorms</a></li>
                    <li><a href="https://www.mwis.org.uk/forecasts/scottish/west-highlands/text">West Highlands</a></li>
                    <li><a href="https://www.mwis.org.uk/forecasts/scottish/the-northwest-highlands/text">NW Highlands</a></li>
                    <li><a href="https://www.mwis.org.uk/">MWIS home</a></li>
                </ul>
            </details>

            <details>
                <summary>SAIS forecasts</summary>
                <ul>
                    <li><a href="https://www.sais.gov.uk/southern-cairngorms/">S Cairngorms</a></li>
                    <li><a href="https://www.sais.gov.uk/northern-cairngorms/">N Cairngorms</a></li>
                    <li><a href="https://www.sais.gov.uk/glencoe/">Glen Coe</a></li>
                    <li><a href="https://www.sais.gov.uk/lochaber/">Lochaber</a></li>
                    <li><a href="https://www.sais.gov.uk/creag-meagaidh/">Creag Meagaidh</a></li>
                    <li><a href="https://www.sais.gov.uk/torridon/">Torridon</a></li>
                    <li><a href="https://www.sais.gov.uk/">SAIS home</a></li>
                </ul>
            </details>
        </div>
    </div>
</div>
</div></body></html>"""

with open("trmnl.html", "w", encoding="utf-8") as f:
    f.write(trmnl_tmpl)
