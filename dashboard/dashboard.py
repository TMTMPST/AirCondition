import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from streamlit_folium import st_folium
import os

# Page Config
st.set_page_config(
    page_title="Air Quality Dashboard - Beijing Stations",
    page_icon="🌫️",
    layout="wide"
)

# Load Data
@st.cache_data
def load_data():
    if os.path.exists('dashboard/all_stations_data.csv'):
        df = pd.read_csv('dashboard/all_stations_data.csv')
    else:
        # Fallback: load from raw data
        import glob
        csv_files = sorted(glob.glob('data/PRSA_Data_*.csv'))
        all_dfs = [pd.read_csv(f) for f in csv_files]
        df = pd.concat(all_dfs, ignore_index=True)
        df = df.groupby('station', group_keys=False).apply(lambda g: g.ffill())
        df = df.groupby('station', group_keys=False).apply(lambda g: g.bfill())
        def classify_aqi(pm25):
            if pm25 <= 12: return 'Good'
            elif pm25 <= 35.4: return 'Moderate'
            elif pm25 <= 55.4: return 'Unhealthy for Sensitive Groups'
            elif pm25 <= 150.4: return 'Unhealthy'
            elif pm25 <= 250.4: return 'Very Unhealthy'
            else: return 'Hazardous'
        df['Air_Quality_Category'] = df['PM2.5'].apply(classify_aqi)

    df['datetime'] = pd.to_datetime(df['datetime']) if 'datetime' in df.columns else pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    return df

@st.cache_data
def load_station_summary():
    if os.path.exists('dashboard/station_summary.csv'):
        return pd.read_csv('dashboard/station_summary.csv')
    return None

df = load_data()
station_summary = load_station_summary()

# Station coordinates (hardcoded for reliability)
STATION_COORDS = {
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

# Sidebar
st.sidebar.header("🔧 Filter Data")

# Station filter
stations = sorted(df['station'].unique())
selected_stations = st.sidebar.multiselect(
    "Select Stations",
    options=stations,
    default=stations
)

# Date range filter
min_date = df['datetime'].min().date()
max_date = df['datetime'].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    start_dt = pd.to_datetime(min_date)
    end_dt = pd.to_datetime(max_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

# Apply filters
main_df = df[
    (df['station'].isin(selected_stations)) &
    (df['datetime'] >= start_dt) &
    (df['datetime'] <= end_dt)
]

# Header
 
st.title("🌫️ Air Quality Analysis Dashboard")
st.markdown("**Multi-Station Analysis — 12 Beijing Monitoring Stations (2013–2017)**")

 
# Key Metrics
 
col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Avg PM2.5", f"{main_df['PM2.5'].mean():.1f} µg/m³")
col2.metric("🔴 Max PM2.5", f"{main_df['PM2.5'].max():.0f} µg/m³")
col3.metric("🌡️ Avg Temp", f"{main_df['TEMP'].mean():.1f} °C")
col4.metric("🏭 Stations", f"{main_df['station'].nunique()}")

 
# Tab Layout
 
tab_map, tab_trend, tab_compare, tab_corr = st.tabs([
    "🗺️ Geospatial Map", "📈 PM2.5 Trends", "📊 Station Comparison", "🔗 Correlation"
])

 
# TAB 1: Geospatial Map (Folium)
 
with tab_map:
    st.subheader("🗺️ Geospatial Analysis — Air Quality by Station")
    st.markdown("Peta menunjukkan rata-rata PM2.5 di setiap stasiun pemantauan. Warna dan ukuran lingkaran menunjukkan tingkat polusi.")

    # Compute filtered per-station averages
    geo_stats = main_df.groupby('station').agg(
        avg_PM25=('PM2.5', 'mean'),
        max_PM25=('PM2.5', 'max'),
        avg_TEMP=('TEMP', 'mean'),
        avg_WSPM=('WSPM', 'mean'),
    ).reset_index()
    geo_stats['lat'] = geo_stats['station'].map(lambda s: STATION_COORDS.get(s, (0,0))[0])
    geo_stats['lon'] = geo_stats['station'].map(lambda s: STATION_COORDS.get(s, (0,0))[1])

    # Create folium map centered on Beijing
    m = folium.Map(location=[39.95, 116.40], zoom_start=10, tiles='OpenStreetMap')

    # Color function based on PM2.5 level
    def get_color(pm25):
        if pm25 <= 35: return 'green'
        elif pm25 <= 75: return 'orange'
        elif pm25 <= 150: return 'red'
        else: return 'darkred'

    for _, row in geo_stats.iterrows():
        color = get_color(row['avg_PM25'])
        popup_text = f"""
        <b>{row['station']}</b><br>
        Avg PM2.5: {row['avg_PM25']:.1f} µg/m³<br>
        Max PM2.5: {row['max_PM25']:.0f} µg/m³<br>
        Avg Temp: {row['avg_TEMP']:.1f} °C<br>
        Avg Wind: {row['avg_WSPM']:.1f} m/s
        """
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=max(8, row['avg_PM25'] / 5),
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{row['station']}: {row['avg_PM25']:.1f} µg/m³",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 999;
                background: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey; font-size: 13px;">
    <b>PM2.5 Legend</b><br>
    🟢 Good (≤35)<br>
    🟠 Moderate (36–75)<br>
    🔴 Unhealthy (76–150)<br>
    🟤 Hazardous (>150)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=900, height=500)

 
# TAB 2: PM2.5 Trends
 
with tab_trend:
    st.subheader("📈 Tren PM2.5 Seiring Waktu")

    # Monthly average per station
    monthly = main_df.copy()
    monthly['year_month'] = monthly['datetime'].dt.to_period('M').astype(str)
    monthly_avg = monthly.groupby(['year_month', 'station'])['PM2.5'].mean().reset_index()

    fig1, ax1 = plt.subplots(figsize=(16, 6))
    for station in selected_stations:
        station_data = monthly_avg[monthly_avg['station'] == station]
        ax1.plot(station_data['year_month'], station_data['PM2.5'], label=station, alpha=0.8, linewidth=1)
    ax1.set_title("Monthly Average PM2.5 per Station", fontsize=14)
    ax1.set_ylabel("PM2.5 (µg/m³)")
    ax1.set_xlabel("Month")
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax1.tick_params(axis='x', rotation=90)
    # Show every 6th label
    ticks = ax1.get_xticks()
    labels = [item.get_text() for item in ax1.get_xticklabels()]
    for i, label in enumerate(ax1.get_xticklabels()):
        if i % 6 != 0:
            label.set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

    # Seasonal pattern
    st.subheader("📅 Pola Bulanan Rata-rata PM2.5")
    season_avg = main_df.groupby('month')['PM2.5'].mean().reset_index()
    fig_season, ax_season = plt.subplots(figsize=(10, 5))
    bars = ax_season.bar(season_avg['month'], season_avg['PM2.5'],
                         color=['#2ecc71' if v <= 50 else '#f39c12' if v <= 100 else '#e74c3c' for v in season_avg['PM2.5']])
    ax_season.set_title("Average PM2.5 by Month (All Selected Stations)", fontsize=14)
    ax_season.set_xlabel("Month")
    ax_season.set_ylabel("PM2.5 (µg/m³)")
    ax_season.set_xticks(range(1, 13))
    ax_season.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    plt.tight_layout()
    st.pyplot(fig_season)

 
# TAB 3: Station Comparison
 
with tab_compare:
    st.subheader("📊 Perbandingan Kualitas Udara antar Stasiun")

    # Station avg PM2.5 bar chart
    station_avg = main_df.groupby('station')['PM2.5'].mean().sort_values(ascending=True).reset_index()
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    colors = ['#2ecc71' if v <= 50 else '#f39c12' if v <= 75 else '#e74c3c' for v in station_avg['PM2.5']]
    ax2.barh(station_avg['station'], station_avg['PM2.5'], color=colors)
    ax2.set_title("Average PM2.5 by Station", fontsize=14)
    ax2.set_xlabel("PM2.5 (µg/m³)")
    plt.tight_layout()
    st.pyplot(fig2)

    # Air Quality Categories Distribution
    st.subheader("🏷️ Distribusi Kategori Kualitas Udara per Stasiun")
    cat_order = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    cat_colors = {'Good': '#2ecc71', 'Moderate': '#f1c40f', 'Unhealthy for Sensitive Groups': '#e67e22',
                  'Unhealthy': '#e74c3c', 'Very Unhealthy': '#9b59b6', 'Hazardous': '#7f1d1d'}

    cat_data = main_df.groupby(['station', 'Air_Quality_Category']).size().unstack(fill_value=0)
    # Normalize to percentage
    cat_pct = cat_data.div(cat_data.sum(axis=1), axis=0) * 100
    # Reorder columns
    existing_cats = [c for c in cat_order if c in cat_pct.columns]
    cat_pct = cat_pct[existing_cats]

    fig3, ax3 = plt.subplots(figsize=(14, 6))
    cat_pct.plot(kind='barh', stacked=True, ax=ax3, color=[cat_colors[c] for c in existing_cats])
    ax3.set_title("Air Quality Category Distribution by Station (%)", fontsize=14)
    ax3.set_xlabel("Percentage (%)")
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig3)

 
# TAB 4: Correlation Analysis
 
with tab_corr:
    st.subheader("🔗 Korelasi Faktor Cuaca dengan PM2.5")

    cols_for_corr = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM']
    corr_data = main_df[cols_for_corr].corr()

    fig4, ax4 = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_data, annot=True, cmap='coolwarm', fmt='.2f', ax=ax4, linewidths=0.5)
    ax4.set_title("Correlation Heatmap", fontsize=14)
    plt.tight_layout()
    st.pyplot(fig4)

    # Scatter: Wind Speed vs PM2.5
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("💨 Wind Speed vs PM2.5")
        fig5, ax5 = plt.subplots(figsize=(8, 6))
        sample = main_df.sample(min(5000, len(main_df)), random_state=42)
        sns.scatterplot(data=sample, x='WSPM', y='PM2.5', hue='station', alpha=0.5, ax=ax5, s=15)
        ax5.set_title("Wind Speed vs PM2.5")
        ax5.legend(fontsize=7, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig5)

    with col_b:
        st.subheader("🌡️ Temperature vs PM2.5")
        fig6, ax6 = plt.subplots(figsize=(8, 6))
        sns.scatterplot(data=sample, x='TEMP', y='PM2.5', hue='station', alpha=0.5, ax=ax6, s=15)
        ax6.set_title("Temperature vs PM2.5")
        ax6.legend(fontsize=7, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig6)

 
# Footer
 
st.markdown("---")
st.caption("Data: Air Quality Dataset — 12 Beijing Monitoring Stations (2013–2017) | Dicoding Final Project")
