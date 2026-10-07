"""
check_data.py
Analyze ALL your records from Supabase (no 1000 row limit).
"""

from supabase import create_client
import pandas as pd
import numpy as np

# Supabase connection
SUPABASE_URL = "https://hyrqaiedlevqzbfhfxpu.supabase.co"
SUPABASE_KEY = "sb_publishable_-nDM7hubn0soFXTqdqm-9g_EnrIxloy"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("BAYOUGUARD DATA ANALYSIS")
print("=" * 60)

# -------------------------------------------
# FETCH ALL RECORDS (NO LIMIT)
# -------------------------------------------
print("\n📊 Fetching ALL records from Supabase...")

# total count
response = supabase.table("flood_gauges").select("*", count="exact").execute()
total_count = response.count

print(f"   Total records in database: {total_count:,}")

# Get all records using pagination
all_data = []
page = 0
page_size = 1000

while len(all_data) < total_count:
    offset = page * page_size
    response = supabase.table("flood_gauges").select("*").range(offset, offset + page_size - 1).execute()
    
    if not response.data:
        break
    
    all_data.extend(response.data)
    print(f"   Fetched {len(all_data):,} / {total_count:,} records...")
    page += 1

df = pd.DataFrame(all_data)

print(f"\n✅ Loaded {len(df):,} records")

# -------------------------------------------
# FIXING: Handle date conversion properly
# -------------------------------------------

print("\n📅 Processing dates...")

# Try different date formats
try:
    # First try: ISO8601 format (with T)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], format='mixed')
    print("   Date format: ISO8601 (with T)")
except:
    try:
        # Second try: Standard format
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        print("   Date format: Standard")
    except:
        # Third try: Force conversion
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors='coerce')
        print("   Date format: Forced conversion")

# Check for any dates that failed to convert
null_dates = df["recorded_at"].isnull().sum()
if null_dates > 0:
    print(f"   ⚠️ {null_dates} records had invalid dates and were skipped")

# Date range
print(f"\n📅 Date range: {df['recorded_at'].min()} to {df['recorded_at'].max()}")
print(f"📅 Total days: {(df['recorded_at'].max() - df['recorded_at'].min()).days}")

# -------------------------------------------
# RISK TIER DISTRIBUTION
# -------------------------------------------
print("\n" + "=" * 40)
print("RISK TIER DISTRIBUTION")
print("=" * 40)
risk_counts = df["risk_tier"].value_counts()
for tier, count in risk_counts.items():
    percentage = (count / len(df)) * 100
    bar = "█" * int(percentage / 2)
    print(f"{tier:10}: {count:6,} ({percentage:5.1f}%) {bar}")

# --------------------------------------------
# DATA QUALITY
# --------------------------------------------

print("\n" + "=" * 40)
print("DATA QUALITY")
print("=" * 40)
missing = df.isnull().sum()
for col, count in missing.items():
    if count > 0 and count < len(df):
        print(f"⚠️ {col}: {count:,} missing ({count/len(df)*100:.1f}%)")

# Check for duplicates
duplicates = df.duplicated(subset=["gauge_id", "recorded_at"]).sum()
if duplicates > 0:
    print(f"⚠️ Duplicate records: {duplicates}")

# --------------------------------------------
# GAUGE STATISTICS
# --------------------------------------------

print(f"\n📊 Unique gauges: {df['gauge_id'].nunique()}")

# Current levels stats
print(f"\n📊 Water Level Statistics:")
print(f"   Min: {df['current_level'].min():.1f} ft")
print(f"   Max: {df['current_level'].max():.1f} ft")
print(f"   Avg: {df['current_level'].mean():.1f} ft")

# Buffer stats
print(f"\n📊 Buffer Statistics (feet until flooding):")
print(f"   Min: {df['buffer'].min():.1f} ft")
print(f"   Max: {df['buffer'].max():.1f} ft")
print(f"   Avg: {df['buffer'].mean():.1f} ft")

# --------------------------------------------
# HIGH/CRITICAL EVENTS
# --------------------------------------------

print("\n" + "=" * 40)
print("HIGH/CRITICAL EVENTS ANALYSIS")
print("=" * 40)

high_critical = df[df["risk_tier"].isin(["HIGH", "CRITICAL"])]
print(f"Total HIGH/CRITICAL events: {len(high_critical):,}")

if len(high_critical) > 0:
    print(f"\nFirst 5 HIGH/CRITICAL events:")
    for idx, row in high_critical.head(5).iterrows():
        print(f"   Gauge {row['gauge_id']}: {row['risk_tier']} at {row['recorded_at']} (buffer: {row['buffer']:.1f} ft)")
    
    # Which gauges have the most HIGH events?
    high_by_gauge = high_critical["gauge_id"].value_counts()
    print(f"\nGauges with most HIGH/CRITICAL events:")
    for gauge_id, count in high_by_gauge.head(5).items():
        print(f"   Gauge {gauge_id}: {count} events")
else:
    print("   No HIGH or CRITICAL events found in the data.")
    print("   This means no major flooding occurred during the collection period.")
    print("   Your model will still learn from MEDIUM events as warnings.")

# -------------------------------------------
# SAMPLE DATA
# -------------------------------------------

print("\n" + "=" * 40)
print("SAMPLE OF YOUR DATA")
print("=" * 40)
print(df.head(10).to_string())

print("\n✅ Data check complete!")
print(f"\n📊 Total records available for ML training: {len(df):,}")
print(f"📊 HIGH/CRITICAL events available: {len(high_critical):,}")

# Recommendation
print("\n💡 RECOMMENDATION:")
if len(high_critical) > 100:
    print("   ✅ You have plenty of HIGH/CRITICAL events! Ready for ML training.")
elif len(high_critical) > 0:
    print("   ⚠️ You have some HIGH/CRITICAL events. ML model will work but may need class weighting.")
else:
    print("   ⚠️ No HIGH/CRITICAL events found. Consider:")
    print("      1. Collect data for longer (wait for next storm)")
    print("      2. Use rule-based system (still works for CAC)")
    print("      3. Train model to predict MEDIUM → HIGH transitions")