"""
BayouGuard FastAPI Backend with ML Model
Provides flood risk assessment using trained Random Forest model.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import math
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

# LOAD ML MODEL (if available)

ML_AVAILABLE = False
model = None
FEATURE_COLUMNS = []

try:
    if os.path.exists("flood_model.pkl") and os.path.exists("feature_columns.pkl"):
        with open("flood_model.pkl", "rb") as f:
            model = pickle.load(f)
        with open("feature_columns.pkl", "rb") as f:
            FEATURE_COLUMNS = pickle.load(f)
        ML_AVAILABLE = True
        print("ML model loaded successfully")
    else:
        print("ML model files not found. Using rule-based fallback.")
except Exception as e:
    print(f"Error loading ML model: {e}")
    ML_AVAILABLE = False


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in miles"""
    R = 3959
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def find_closest_gauge(lat, lng):
    """Find the flood gauge closest to the user's address"""
    url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&regionId=4&regionId=10&regionId=22&regionId=1&regionId=14&regionId=18&regionId=19&regionId=23&regionId=20&timeSpan=7&dt=1779069600000"
    headers = {"Referer": "https://www.harriscountyfws.org/"}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception:
        return None, float('inf')
    
    closest = None
    closest_distance = float('inf')
    
    for site in data.get("features", []):
        try:
            props = site.get("properties", {})
            geometry = site.get("geometry", {})
            coords = geometry.get("coordinates", [0, 0])
            
            if len(coords) < 2:
                continue
            
            try:
                gauge_lng = float(coords[0])
                gauge_lat = float(coords[1])
            except (ValueError, TypeError):
                continue
            
            distance = haversine(lat, lng, gauge_lat, gauge_lng)
            
            if distance < closest_distance:
                closest_distance = distance
                closest = props
        except Exception:
            continue
    
    return closest, closest_distance


def get_gauge_history(gauge_id):
    """Fetch historical data for a gauge from Supabase"""
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")       "Security Fix: Moving Supabase Keys to env"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("flood_gauges").select("*").eq("gauge_id", gauge_id).order("recorded_at", desc=True).limit(30).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return pd.DataFrame()


def calculate_risk_with_ml(gauge, distance_miles):
    """Calculate risk using ML model"""
    try:
        stream = gauge["StreamData"][0]
        current = stream["CurrentLevel"]
        flood = stream["ChannelInfo"]["FloodLevelIndicator"]
        buffer = flood - current
        
        gauge_id = gauge.get("SiteId")
        
        hist_df = get_gauge_history(gauge_id)
        
        if len(hist_df) < 24:
            return calculate_risk_rule_based(gauge, distance_miles)
        
        hist_df = hist_df.sort_values("recorded_at")
        recent_levels = hist_df["current_level"].tolist()
        
        if len(recent_levels) >= 4:
            rate_of_rise = (current - recent_levels[-1]) * 4 if recent_levels else 0
        else:
            rate_of_rise = 0
        
        level_1h_ago = recent_levels[-1] if len(recent_levels) >= 1 else current
        level_3h_ago = recent_levels[-3] if len(recent_levels) >= 3 else current
        level_6h_ago = recent_levels[-6] if len(recent_levels) >= 6 else current
        
        buffer_vals = hist_df["buffer"].tolist()[:4]
        buffer_1h_avg = sum(buffer_vals) / len(buffer_vals) if buffer_vals else buffer
        
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        
        buffer_pct = max(0, (buffer / flood) * 100) if flood > 0 else 0
        
        features = pd.DataFrame([[
            current, buffer, rate_of_rise, level_1h_ago, level_3h_ago,
            level_6h_ago, buffer_1h_avg, hour, day_of_week, buffer_pct
        ]], columns=FEATURE_COLUMNS)
        
        flood_probability = model.predict_proba(features)[0][1]
        score = int(flood_probability * 100)
        
        if score <= 25:
            tier = "LOW"
        elif score <= 50:
            tier = "MEDIUM"
        elif score <= 75:
            tier = "HIGH"
        else:
            tier = "CRITICAL"
        
        return tier, score, buffer, current, flood, distance_miles
        
    except Exception as e:
        print(f"ML error: {e}, falling back to rule-based")
        return calculate_risk_rule_based(gauge, distance_miles)


def calculate_risk_rule_based(gauge, distance_miles):
    """Fallback rule-based risk calculation"""
    stream = gauge["StreamData"][0]
    current = stream["CurrentLevel"]
    flood = stream["ChannelInfo"]["FloodLevelIndicator"]
    buffer = flood - current
    
    if buffer <= 0:
        tier = "CRITICAL"
        score = 95
    elif buffer <= 2:
        tier = "HIGH"
        score = 75
    elif buffer <= 5:
        tier = "MEDIUM"
        score = 50
    elif buffer <= 10:
        tier = "LOW"
        score = 25
    else:
        tier = "SAFE"
        score = 10
    
    return tier, score, buffer, current, flood, distance_miles


def calculate_risk_from_gauge(gauge, distance_miles):
    """Main risk calculation function (uses ML if available)"""
    if ML_AVAILABLE and model is not None:
        return calculate_risk_with_ml(gauge, distance_miles)
    else:
        return calculate_risk_rule_based(gauge, distance_miles)


@app.get("/risk")
def get_risk(address: str = Query(...), lat: float = Query(...), lng: float = Query(...)):
    """Get flood risk for a specific address"""
    gauge, distance = find_closest_gauge(lat, lng)
    
    if not gauge:
        return {"error": "No flood gauge found near this location"}
    
    tier, score, buffer, current, flood, distance = calculate_risk_from_gauge(gauge, distance)
    
    messages = {
        "en": f"Flood risk at {address} is {tier} ({score}%). The nearest gauge is {distance:.1f} miles away with water level at {current} ft (floods at {flood} ft).",
        "es": f"El riesgo de inundación en {address} es {tier} ({score}%). El medidor más cercano está a {distance:.1f} millas con nivel de agua en {current} ft (inunda en {flood} ft).",
        "vi": f"Nguy cơ lũ lụt tại {address} là {tier} ({score}%). Máy đo gần nhất cách {distance:.1f} dặm với mực nước ở {current} ft (ngập ở {flood} ft)."
    }
    
    return {
        "address": address,
        "risk_tier": tier,
        "risk_score": score,
        "buffer_ft": round(buffer, 1),
        "nearest_gauge_distance_miles": round(distance, 2),
        "message": messages["en"],
        "model_used": "ML" if ML_AVAILABLE else "Rule-based (fallback)"
    }


@app.get("/gauges")
def get_all_gauges():
    """Get all 39 flood gauges with locations and risk levels"""
    url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&regionId=4&regionId=10&regionId=22&regionId=1&regionId=14&regionId=18&regionId=19&regionId=23&regionId=20&timeSpan=7&dt=1779069600000"
    headers = {"Referer": "https://www.harriscountyfws.org/"}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}
    
    result = []
    
    for site in data.get("features", []):
        try:
            props = site.get("properties", {})
            geometry = site.get("geometry", {})
            coordinates = geometry.get("coordinates", [0, 0])
            
            if len(coordinates) < 2:
                continue
            
            try:
                longitude = float(coordinates[0])
                latitude = float(coordinates[1])
            except (ValueError, TypeError):
                continue
            
            stream_data = props.get("StreamData", [])
            if not stream_data:
                continue
                
            stream = stream_data[0]
            current = stream.get("CurrentLevel", 0)
            
            channel_info = stream.get("ChannelInfo", {})
            flood = channel_info.get("FloodLevelIndicator")
            
            if flood is None or flood == 999:
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
            
            result.append({
                "id": props.get("SiteId"),
                "latitude": latitude,
                "longitude": longitude,
                "current_level_ft": current,
                "flood_level_ft": flood,
                "buffer_ft": round(buffer, 1),
                "risk_tier": risk
            })
        except Exception:
            continue
    
    return {"count": len(result), "gauges": result}


@app.get("/")
def root():
    """Root endpoint for health checks"""
    return {
        "message": "BayouGuard API is running!",
        "model_status": "Active (ML)" if ML_AVAILABLE else "Fallback (Rule-based)",
        "endpoints": {
            "/risk": "GET - Get flood risk for an address (requires lat, lng, address)",
            "/gauges": "GET - Get all flood gauges with risk levels",
            "/docs": "GET - Interactive API documentation"
        }
    }
