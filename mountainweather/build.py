import requests
from bs4 import BeautifulSoup
import datetime

# URLs
urls = {
    'mwis_west': 'https://www.mwis.org.uk/forecasts/scottish/west-highlands/text',
    'mwis_cairngorms': 'https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text',
    'mwis_se_highlands': 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text',
    'sais_n_cairngorms': 'https://www.sais.gov.uk/northern-cairngorms/',
    'sais_s_cairngorms': 'https://www.sais.gov.uk/southern-cairngorms/',
    'sais_lochaber': 'https://www.sais.gov.uk/lochaber/',
    'sais_glencoe': 'https://www.sais.gov.uk/glencoe/'
}

headers = {'User-Agent': 'Mozilla/5.0'}
data = {}

# Scrape MWIS
for key in ['mwis_west', 'mwis_cairngorms', 'mwis_se_highlands']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Find Headline
        headline_tag = soup.find(lambda tag: tag.name == "h3" and "Headline" in tag.text)
        headline = headline_tag.find_next_sibling('p').text.strip() if headline_tag else "Headline unavailable"
        
        # Find Summary
        summary_tag = soup.find(lambda tag: tag.name == "h3" and "Summary" in tag.text)
        summary = summary_tag.find_next_sibling('p').text.strip() if summary_tag else "Summary unavailable"
        
        data[key] = f"<div class='headline'>\"{headline}\"</div><div>{summary}</div>"
    except Exception:
        data[key] = "Forecast currently unavailable."

# Scrape SAIS
for key in ['sais_n_cairngorms', 'sais_s_cairngorms', 'sais_lochaber', 'sais_glencoe']:
    try:
        res = requests.get(urls[key], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        if "finished for the winter" in res.text:
            data[key] = "Reporting finished for the winter season."
        else:
            hazard = soup.select_one('.hazard-level h2, .forecast-text p')
            data[key] = hazard.text.strip() if hazard else "Live hazard data not found."
    except Exception:
         data[key] = "Report unavailable."

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mountain Weather Dashboard</title>
<style>
  body {{ font-family: sans-serif; background: #fff; color: #000; margin: 0; padding: 10px; line-height: 1.4; }}
  h1 {{ font-size: 1.8em; border-bottom: 3px solid #000; padding-bottom: 5px; margin-top: 0; text-align: center; }}
  h2 {{ font-size: 1.3em; margin: 0 0 10px 0; background: #000; color: #fff; padding: 5px 10px; }}
  p {{ margin: 5px 0; font-size: 1.1em; }}
  .status {{ text-align: center; font-size: 0.8em; font-style: italic; margin-bottom: 15px; font-weight: bold; }}
  .region {{ border: 2px solid #000; margin-bottom: 15px; padding: 0; }}
  .region-content {{ padding: 10px; }}
  .headline {{ font-weight: bold; font-style: italic; margin-bottom: 10px; border-bottom: 1px dashed #000; padding-bottom: 5px; }}
</style>
</head>
<body>
  <h1>Mountain Dashboard</h1>
  <div class="status">Last automatically updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>

  <div class="region">
    <h2>SAIS Avalanche Conditions</h2>
    <div class="region-content">
      <p><strong>Northern Cairngorms:</strong> {data['sais_n_cairngorms']}</p>
      <p><strong>Southern Cairngorms:</strong> {data['sais_s_cairngorms']}</p>
      <p><strong>Lochaber:</strong> {data['sais_lochaber']}</p>
      <p><strong>Glencoe:</strong> {data['sais_glencoe']}</p>
    </div>
  </div>

  <div class="region"><h2>West Highlands (MWIS)</h2><div class="region-content">{data['mwis_west']}</div></div>
  <div class="region"><h2>Cairngorms & Monadhliath (MWIS)</h2><div class="region-content">{data['mwis_cairngorms']}</div></div>
  <div class="region"><h2>Southeastern Highlands (MWIS)</h2><div class="region-content">{data['mwis_se_highlands']}</div></div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
