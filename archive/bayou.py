import requests 
import json 
url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000" 
headers = {"Referer": "https://www.harriscountyfws.org/"} 
response = requests.get(url, headers=headers) 
data = response.json() 
sites = data["features"] 
print("BayouGuard - Harris County Flood Gauges\n") 
for site in sites[:5]: 
  props = site["properties"] 
  site_name = props.get("SiteName", "Unknown") 
  stream = props["StreamData"][0] 
  current = stream["CurrentLevel"] 
  flood = stream["ChannelInfo"]["FloodLevelIndicator"] 
  gap = flood - current 
  print(f"{site_name}: {current} ft / Flood at {flood} ft (gap: {gap:.1f} ft)") 
