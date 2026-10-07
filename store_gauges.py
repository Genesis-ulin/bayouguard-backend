import requests
import os                     #Adding 
from supabase import create_client

# Supabase connection  (Security Fix: Moving Supabase Keys to Environment)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Harris County flood data
url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"
headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

print("BayouGuard - Storing Flood Data to Supabase\n")

count = 0
for site in sites:
    props = site["properties"]
    site_id = props.get("SiteId", 0)
    
    # Skip if no StreamData
    stream_data = props.get("StreamData")
    if not stream_data or len(stream_data) == 0:
        continue
        
    stream = stream_data[0]
    current = stream.get("CurrentLevel", 0)
    
    channel_info = stream.get("ChannelInfo")
    if not channel_info:
        continue
        
    flood = channel_info.get("FloodLevelIndicator", 999)
    
    # Skip if flood level is not set
    if flood == 999 or flood is None:
        continue
        
    buffer = flood - current
    
    # Calculate risk tier
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
    
    # Store in Supabase
    data_to_store = {
        "gauge_id": site_id,
        "current_level": current,
        "flood_level": flood,
        "buffer": buffer,
        "risk_tier": risk
    }
    
    try:
        result = supabase.table("flood_gauges").insert(data_to_store).execute()
        count += 1
        print(f"✅ Stored gauge {site_id}: {risk} risk (buffer: {buffer:.1f} ft)")
    except Exception as e:
        print(f"❌ Failed to store gauge {site_id}: {e}")

print(f"\n✅ Successfully stored {count} gauges to Supabase!")
