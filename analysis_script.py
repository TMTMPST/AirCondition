import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Create dashboard directory if it doesn't exist
os.makedirs('dashboard', exist_ok=True)

# 1. Gather Data - ALL 12 Stations
print("Loading all 12 station datasets...")
csv_files = sorted(glob.glob('data/PRSA_Data_*.csv'))

all_dfs = []
for f in csv_files:
    station_df = pd.read_csv(f)
    all_dfs.append(station_df)
    print(f"  Loaded: {os.path.basename(f)} -> {len(station_df)} rows, station: {station_df['station'].iloc[0]}")

df = pd.concat(all_dfs, ignore_index=True)
print(f"\nTotal combined rows: {len(df)}")
print(f"Stations: {df['station'].unique()}")

# 2. Assess Data
print("\nData Info:")
print(df.info())
print("\nMissing Values:")
print(df.isna().sum())
print("\nDuplicates:", df.duplicated().sum())

# 3. Clean Data
print("\nCleaning data...")
# Forward fill per station (time-series)
df = df.groupby('station', group_keys=False).apply(lambda g: g.ffill())
# Backward fill remaining NaNs at the start
df = df.groupby('station', group_keys=False).apply(lambda g: g.bfill())

# Create datetime column
df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])

# Air Quality Categories (US EPA PM2.5 standard)
def classify_aqi(pm25):
    if pm25 <= 12: return 'Good'
    elif pm25 <= 35.4: return 'Moderate'
    elif pm25 <= 55.4: return 'Unhealthy for Sensitive Groups'
    elif pm25 <= 150.4: return 'Unhealthy'
    elif pm25 <= 250.4: return 'Very Unhealthy'
    else: return 'Hazardous'

df['Air_Quality_Category'] = df['PM2.5'].apply(classify_aqi)

print(f"\nAfter cleaning - Missing Values: {df.isna().sum().sum()}")

# 4. Save cleaned data
print("\nSaving cleaned combined data to dashboard/all_stations_data.csv...")
df.to_csv('dashboard/all_stations_data.csv', index=False)

# Also save per-station summary for quick geo loading
station_coords = {
    'Aotizhongxin': (39.9822, 116.3972),
    'Changping':    (40.2180, 116.2310),
    'Dingling':     (40.2920, 116.2200),
    'Dongsi':       (39.9290, 116.4170),
    'Guanyuan':     (39.9290, 116.3390),
    'Gucheng':      (39.9140, 116.1840),
    'Huairou':      (40.3280, 116.6280),
    'Nongzhanguan': (39.9370, 116.4610),
    'Shunyi':       (40.1270, 116.6550),
    'Tiantan':      (39.8820, 116.4070),
    'Wanliu':       (39.9870, 116.2870),
    'Wanshouxigong':(39.8780, 116.3520),
}

station_summary = df.groupby('station').agg(
    avg_PM25=('PM2.5', 'mean'),
    max_PM25=('PM2.5', 'max'),
    avg_PM10=('PM10', 'mean'),
    avg_TEMP=('TEMP', 'mean'),
    avg_WSPM=('WSPM', 'mean'),
    avg_RAIN=('RAIN', 'mean'),
).reset_index()

station_summary['lat'] = station_summary['station'].map(lambda s: station_coords.get(s, (0,0))[0])
station_summary['lon'] = station_summary['station'].map(lambda s: station_coords.get(s, (0,0))[1])

station_summary.to_csv('dashboard/station_summary.csv', index=False)
print("Station summary saved to dashboard/station_summary.csv")
print("\nStation Summary:")
print(station_summary.to_string())

print("\nAnalysis complete!")
