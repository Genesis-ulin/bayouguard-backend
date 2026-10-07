"""
train_model.py
Train a Random Forest model to predict HIGH/CRITICAL flood events.
Uses 418k+ records from Supabase.
"""


from supabase import create_client
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import pickle
import warnings
warnings.filterwarnings('ignore')


# CONFIGURATION


SUPABASE_URL = "https://hyrqaiedlevqzbfhfxpu.supabase.co"
SUPABASE_KEY = "sb_publishable_-nDM7hubn0soFXTqdqm-9g_EnrIxloy"

print("=" * 60)
print("BAYOUGUARD ML TRAINING")
print("=" * 60)


# STEP 1: LOAD ALL DATA


print("\n📊 Loading all data from Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get total count
response = supabase.table("flood_gauges").select("*", count="exact").execute()
total_count = response.count
print(f"   Total records: {total_count:,}")

# Fetch all data with pagination
all_data = []
page = 0
page_size = 1000

while len(all_data) < total_count:
    offset = page * page_size
    response = supabase.table("flood_gauges").select("*").range(offset, offset + page_size - 1).execute()
    if not response.data:
        break
    all_data.extend(response.data)
    print(f"   Loaded {len(all_data):,} / {total_count:,} records...")
    page += 1

df = pd.DataFrame(all_data)

print(f"\n✅ Loaded {len(df):,} records")


# FIX: Handle date conversion properly


print("\n📅 Processing dates...")
# Use format='ISO8601' to handle the timestamp format without milliseconds
df["recorded_at"] = pd.to_datetime(df["recorded_at"], format='ISO8601')
print("   ✅ Dates converted using ISO8601 format")

# Check for any dates that failed to convert
null_dates = df["recorded_at"].isnull().sum()
if null_dates > 0:
    print(f"   ⚠️ {null_dates} records had invalid dates and were skipped")

df = df.sort_values(["gauge_id", "recorded_at"])

print(f"📅 Date range: {df['recorded_at'].min()} to {df['recorded_at'].max()}")


# STEP 2: CREATE FEATURES


print("\n🔧 Engineering features...")

# Rate of rise (how fast water is changing per hour)
df["rate_of_rise"] = df.groupby("gauge_id")["current_level"].diff() * 4

# Lag features (historical context)
df["level_1h_ago"] = df.groupby("gauge_id")["current_level"].shift(4)
df["level_3h_ago"] = df.groupby("gauge_id")["current_level"].shift(12)
df["level_6h_ago"] = df.groupby("gauge_id")["current_level"].shift(24)

# (removed buffer_1h_avg - leaked the target)

# Time features
df["hour"] = df["recorded_at"].dt.hour
df["day_of_week"] = df["recorded_at"].dt.dayofweek

# (removed buffer_pct - leaked the target)


# STEP 3: CREATE TARGET VARIABLE


print("\n🎯 Creating target variable (predicting HIGH/CRITICAL)...")

# Target: 1 if risk is HIGH or CRITICAL, 0 otherwise
df["target"] = df["risk_tier"].isin(["HIGH", "CRITICAL"]).astype(int)

print(f"   Target distribution:")
print(f"      Normal (0): {(df['target'] == 0).sum():,} ({100 - df['target'].mean()*100:.1f}%)")
print(f"      HIGH/CRITICAL (1): {df['target'].sum():,} ({df['target'].mean()*100:.1f}%)")


# STEP 4: PREPARE FEATURES


print("\n📐 Preparing feature matrix...")

feature_columns = [
    "current_level",
    "rate_of_rise",
    "level_1h_ago",
    "level_3h_ago",
    "level_6h_ago",
    "hour",
    "day_of_week"

]

# Drop rows with missing values
df_clean = df.dropna(subset=feature_columns + ["target"])
X = df_clean[feature_columns]
y = df_clean["target"]

print(f"   Features: {len(feature_columns)}")
print(f"   Training samples: {len(X):,}")
print(f"   HIGH/CRITICAL events: {y.sum():,} ({y.mean()*100:.2f}%)")


# STEP 5: TRAIN/TEST SPLIT


print("\n Splitting data (80% train, 20% test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   Train: {len(X_train):,} samples")
print(f"   Test: {len(X_test):,} samples")


# STEP 6: TRAIN MODEL


print("\n Training Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    min_samples_split=10,
    min_samples_leaf=5,
    class_weight="balanced",  # Handles the imbalance!
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)


# STEP 7: EVALUATE MODEL


print(" Evaluating model...")

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

accuracy = model.score(X_test, y_test)
auc = roc_auc_score(y_test, y_pred_proba)

print(f"\n   Accuracy: {accuracy:.2%}")
print(f"   AUC Score: {auc:.2%}")

print("\n   Classification Report:")
print("   " + "-" * 40)
print(classification_report(y_test, y_pred, target_names=["Normal", "HIGH/CRITICAL"]))

print("\n   Confusion Matrix:")
print("   " + "-" * 40)
cm = confusion_matrix(y_test, y_pred)
print(f"   Correctly predicted NORMAL: {cm[0,0]:,}")
print(f"   False ALARMS (predicted HIGH but was NORMAL): {cm[0,1]:,}")
print(f"   MISSED (was HIGH but predicted NORMAL): {cm[1,0]:,}")
print(f"   Correctly predicted HIGH/CRITICAL: {cm[1,1]:,}")

# Feature importance
print("\n   Top 5 Most Important Features:")
feature_importance = pd.DataFrame({
    "feature": feature_columns,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

for _, row in feature_importance.head(5).iterrows():
    bar = "█" * int(row["importance"] * 50)
    print(f"      {row['feature']:15}: {row['importance']:.2%} {bar}")


# STEP 8: SAVE MODEL


print(" Saving model...")
with open("flood_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("feature_columns.pkl", "wb") as f:
    pickle.dump(feature_columns, f)

print("  Model saved as 'flood_model.pkl'")
print("  Feature columns saved as 'feature_columns.pkl'")


# SUMMARY


print("\n" + "=" * 60)
print("TRAINING COMPLETE!")
print("=" * 60)
print(f" Final Model Stats:")
print(f"   Training samples: {len(X_train):,}")
print(f"   Test samples: {len(X_test):,}")
print(f"   Features: {len(feature_columns)}")
print(f"   Accuracy: {accuracy:.2%}")
print(f"   AUC Score: {auc:.2%}")

if auc > 0.85:
    print(" EXCELLENT! Your model is ready for production.")
elif auc > 0.75:
    print(" GOOD! Your model will work well.")
else:
    print(" Your model needs improvement.")