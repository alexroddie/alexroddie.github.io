<?php
// ==========================================
// CONFIGURATION
// ==========================================
$cache_file = __DIR__ . '/forecast_cache.json';
$cache_time = 3600; // 1 hour (in seconds)

// URLs to scrape
$sources = [
    'mwis_west' => 'https://www.mwis.org.uk/forecasts/scottish/west-highlands/text',
    'mwis_cairngorms' => 'https://www.mwis.org.uk/forecasts/scottish/cairngorms-np-and-monadhliath/text',
    'mwis_se_highlands' => 'https://www.mwis.org.uk/forecasts/scottish/southeastern-highlands/text',
    'sais_n_cairngorms' => 'https://www.sais.gov.uk/northern-cairngorms/',
    'sais_s_cairngorms' => 'https://www.sais.gov.uk/southern-cairngorms/',
    'sais_lochaber' => 'https://www.sais.gov.uk/lochaber/',
    'sais_glencoe' => 'https://www.sais.gov.uk/glencoe/'
];

// ==========================================
// HELPER FUNCTIONS
// ==========================================

// Safely fetch HTML, pretending to be a normal web browser so we don't get blocked
function fetch_html($url) {
    $options = [
        "http" => [
            "header" => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36\r\n",
            "timeout" => 10 // Don't hang forever if a site is down
        ]
    ];
    $context = stream_context_create($options);
    $html = @file_get_contents($url, false, $context);
    return $html;
}

// Scrape MWIS Text Pages
function parse_mwis($html) {
    if (!$html) return "Forecast currently unavailable.";
    
    // Suppress DOM warnings from poorly formatted HTML
    libxml_use_internal_errors(true);
    $dom = new DOMDocument();
    @$dom->loadHTML($html);
    $xpath = new DOMXPath($dom);
    
    // Extract Headline
    $headline_nodes = $xpath->query("//h3[contains(text(), 'Headline')]/following-sibling::p");
    $headline = $headline_nodes->length > 0 ? trim($headline_nodes->item(0)->nodeValue) : "Headline unavailable";

    // Extract the General Summary (Usually the first paragraph under 'Summary for all mountain areas')
    $summary_nodes = $xpath->query("//h3[contains(text(), 'Summary')]/following-sibling::p");
    $summary = $summary_nodes->length > 0 ? trim($summary_nodes->item(0)->nodeValue) : "Summary unavailable";

    return [
        'headline' => $headline,
        'summary' => $summary
    ];
}

// Scrape SAIS Pages
function parse_sais($html) {
    if (!$html) return "Avalanche report unavailable.";
    
    libxml_use_internal_errors(true);
    $dom = new DOMDocument();
    @$dom->loadHTML($html);
    $xpath = new DOMXPath($dom);
    
    // Check if the season is over (SAIS posts a specific message when finished)
    $finished_nodes = $xpath->query("//p[contains(text(), 'finished for the winter')]");
    if ($finished_nodes->length > 0) {
        return "Reporting finished for the winter season.";
    }

    // Try to find the Hazard Level Text (High, Considerable, Moderate, Low)
    $hazard_nodes = $xpath->query("//div[contains(@class, 'hazard-level')]//h2 | //div[contains(@class, 'forecast-text')]//p");
    
    $report = "";
    if ($hazard_nodes->length > 0) {
        foreach($hazard_nodes as $node) {
            $text = trim($node->nodeValue);
            if (!empty($text)) {
                $report .= $text . " ";
                break; // Just grab the first main summary paragraph to save Kindle screen space
            }
        }
    } else {
        $report = "Live hazard data not found on page. Check SAIS website directly.";
    }
    
    return trim($report);
}

// ==========================================
// MAIN LOGIC (CACHE OR FETCH)
// ==========================================
$forecast_data = [];

// Check if cache exists and is fresh
if (file_exists($cache_file) && (time() - filemtime($cache_file) < $cache_time)) {
    $forecast_data = json_decode(file_get_contents($cache_file), true);
    $status = "Loaded from Cache (Updates hourly)";
} else {
    // Cache is old or missing. Fetch fresh data.
    $status = "Live Data Fetched & Cached";
    
    // Fetch MWIS
    $forecast_data['mwis_west'] = parse_mwis(fetch_html($sources['mwis_west']));
    $forecast_data['mwis_cairngorms'] = parse_mwis(fetch_html($sources['mwis_cairngorms']));
    $forecast_data['mwis_se_highlands'] = parse_mwis(fetch_html($sources['mwis_se_highlands']));
    
    // Fetch SAIS
    $forecast_data['sais_n_cairngorms'] = parse_sais(fetch_html($sources['sais_n_cairngorms']));
    $forecast_data['sais_s_cairngorms'] = parse_sais(fetch_html($sources['sais_s_cairngorms']));
    $forecast_data['sais_lochaber'] = parse_sais(fetch_html($sources['sais_lochaber']));
    $forecast_data['sais_glencoe'] = parse_sais(fetch_html($sources['sais_glencoe']));

    // Save to cache
    file_put_contents($cache_file, json_encode($forecast_data));
}

// Function to safely output array data
function display_mwis($data) {
    if (is_array($data)) {
        return "<div class='headline'>\"" . htmlspecialchars($data['headline']) . "\"</div>" . 
               "<div>" . htmlspecialchars($data['summary']) . "</div>";
    }
    return htmlspecialchars($data);
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mountain Weather Dashboard</title>
<style>
  /* Kindle Paperwhite / E-Ink Optimized CSS */
  body {
    font-family: sans-serif;
    background-color: #ffffff;
    color: #000000;
    margin: 0;
    padding: 10px;
    line-height: 1.4;
  }
  h1 {
    font-size: 1.8em;
    border-bottom: 3px solid #000;
    padding-bottom: 5px;
    margin-top: 0;
    text-align: center;
  }
  h2 {
    font-size: 1.3em;
    margin-top: 0;
    margin-bottom: 10px;
    background: #000;
    color: #fff;
    padding: 5px 10px;
  }
  p {
    margin: 5px 0;
    font-size: 1.1em;
  }
  .system-status {
    text-align: center;
    font-size: 0.8em;
    font-style: italic;
    margin-bottom: 15px;
  }
  .region {
    border: 2px solid #000;
    margin-bottom: 15px;
    padding: 0;
  }
  .region-content {
    padding: 10px;
  }
  .headline {
    font-weight: bold;
    font-style: italic;
    margin-bottom: 10px;
    border-bottom: 1px dashed #000;
    padding-bottom: 5px;
  }
</style>
</head>
<body>

  <h1>Mountain Dashboard</h1>
  <div class="system-status"><?php echo $status; ?> | Last updated: <?php echo date('H:i'); ?></div>

  <div class="region">
    <h2>SAIS Avalanche Conditions</h2>
    <div class="region-content">
      <p><strong>Northern Cairngorms:</strong> <?php echo htmlspecialchars($forecast_data['sais_n_cairngorms']); ?></p>
      <p><strong>Southern Cairngorms:</strong> <?php echo htmlspecialchars($forecast_data['sais_s_cairngorms']); ?></p>
      <p><strong>Lochaber:</strong> <?php echo htmlspecialchars($forecast_data['sais_lochaber']); ?></p>
      <p><strong>Glencoe:</strong> <?php echo htmlspecialchars($forecast_data['sais_glencoe']); ?></p>
    </div>
  </div>

  <div class="region">
    <h2>West Highlands (MWIS)</h2>
    <div class="region-content">
      <?php echo display_mwis($forecast_data['mwis_west']); ?>
    </div>
  </div>

  <div class="region">
    <h2>Cairngorms & Monadhliath (MWIS)</h2>
    <div class="region-content">
      <?php echo display_mwis($forecast_data['mwis_cairngorms']); ?>
    </div>
  </div>

  <div class="region">
    <h2>Southeastern Highlands (MWIS)</h2>
    <div class="region-content">
      <?php echo display_mwis($forecast_data['mwis_se_highlands']); ?>
    </div>
  </div>

</body>
</html>
