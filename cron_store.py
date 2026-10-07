import requests
from supabase import create_client
import datetime
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&regionId=4&regionId=10&regionId=22&regionId=1&regionId=14&regionId=18&regionId=19&regionId=23&regionId=20&timeSpan=7&dt=1779069600000"
headers = {"Referer": "https://www.harriscountyfws.org/"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"Error fetching data: {e}")
    exit(1)

sites = data.get("features", [])
count = 0

for site in sites:
    try:
        props = site.get("properties", {})
        site_id = props.get("SiteId")
        if site_id is None:
            continue
            
        stream_data = props.get("StreamData")
        if not stream_data:
            continue
            
        stream = stream_data[0]
        current = stream.get("CurrentLevel")
        if current is None:
            continue
            
        channel = stream.get("ChannelInfo", {})
        flood = channel.get("FloodLevelIndicator")
        if flood is None:
            continue
            
        buffer = flood - current
        
        if buffer <= 0:
            risk = "CRITICAL"
        elif buffer <= 2:
            risk = "HIGH"
        elif buffer <= 5:
            risk = "MEDIUM"
        elif buffer <= 10:
            risk = "LOW"
        else:
            risk = "SAFE"
        
        supabase.table("flood_gauges").insert({
            "gauge_id": site_id,
            "current_level": current,
            "flood_level": flood,
            "buffer": buffer,
            "risk_tier": risk
        }).execute()
        count += 1
        
    except Exception as e:
        print(f"Error processing gauge: {e}")
        continue

print(f"{datetime.datetime.now()}: Stored {count} gauges")
