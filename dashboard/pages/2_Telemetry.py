import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Telemetry - IntelliTrace", page_icon="📈", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    h1, h2, h3 { color: #e0e0e0 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #4fc3f7 !important; }
</style>
""", unsafe_allow_html=True)

import api_client as api

if not st.session_state.get("token"):
    st.warning("Please login first from the Home page.")
    st.stop()

st.markdown("# 📈 Telemetry & Analytics")

try:
    devices = api.list_devices()
except Exception:
    st.error("Failed to load devices.")
    st.stop()

if not devices:
    st.info("No devices available. Pair a device first.")
    st.stop()

device_options = {d["device_name"]: d["id"] for d in devices}
selected_name = st.selectbox("Select Device", list(device_options.keys()))
device_id = device_options[selected_name]

days = st.slider("Time Range (days)", 1, 90, 7)

try:
    history = api.get_telemetry_history(device_id, limit=200)
except Exception:
    history = []

df = pd.DataFrame(history) if history else pd.DataFrame()
if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

tab_vitals, tab_activity, tab_location, tab_advanced, tab_raw = st.tabs(
    ["❤️ Vitals", "🏃 Activity", "📍 Location", "🔬 Advanced Sensors", "📋 Raw Data"]
)

with tab_vitals:
    if df.empty:
        st.info("No telemetry data available yet.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        if filtered.empty:
            st.info(f"No data in the last {days} days.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            if "heart_rate" in filtered.columns:
                hr = filtered["heart_rate"].dropna()
                if not hr.empty:
                    col1.metric("Avg Heart Rate", f"{hr.mean():.0f} bpm")
                    col2.metric("Max Heart Rate", f"{hr.max()} bpm")
            if "sp_o2" in filtered.columns:
                sp = filtered["sp_o2"].dropna()
                if not sp.empty:
                    col3.metric("Avg SpO2", f"{sp.mean():.1f}%")
            if "skin_temperature" in filtered.columns:
                temp = filtered["skin_temperature"].dropna()
                if not temp.empty:
                    col4.metric("Avg Temp", f"{temp.mean():.1f}°C")

            st.divider()

            if "heart_rate" in filtered.columns:
                hr_data = filtered[["timestamp", "heart_rate"]].dropna()
                if not hr_data.empty:
                    fig = px.line(hr_data, x="timestamp", y="heart_rate",
                                  title="Heart Rate Over Time",
                                  labels={"heart_rate": "BPM", "timestamp": "Time"},
                                  color_discrete_sequence=["#ff6b6b"])
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

            if "sp_o2" in filtered.columns:
                sp_data = filtered[["timestamp", "sp_o2"]].dropna()
                if not sp_data.empty:
                    fig = px.line(sp_data, x="timestamp", y="sp_o2",
                                  title="SpO2 Levels Over Time",
                                  labels={"sp_o2": "SpO2 %", "timestamp": "Time"},
                                  color_discrete_sequence=["#4fc3f7"])
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                      yaxis=dict(range=[85, 100]))
                    st.plotly_chart(fig, use_container_width=True)

            if "skin_temperature" in filtered.columns:
                temp_data = filtered[["timestamp", "skin_temperature"]].dropna()
                if not temp_data.empty:
                    fig = px.line(temp_data, x="timestamp", y="skin_temperature",
                                  title="Skin Temperature Over Time",
                                  labels={"skin_temperature": "Temp °C", "timestamp": "Time"},
                                  color_discrete_sequence=["#ffa726"])
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

            # Respiration rate
            if "respiration_rate" in filtered.columns:
                rr_data = filtered[["timestamp", "respiration_rate"]].dropna()
                if not rr_data.empty:
                    fig = px.line(rr_data, x="timestamp", y="respiration_rate",
                                  title="Respiration Rate Over Time",
                                  labels={"respiration_rate": "Breaths/min", "timestamp": "Time"},
                                  color_discrete_sequence=["#66bb6a"])
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

with tab_activity:
    try:
        activity = api.get_activity(device_id, days=days)
    except Exception:
        activity = {}

    if activity:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Steps", f"{activity.get('total_steps', 0):,}")
        avg_spd = activity.get("avg_speed")
        c2.metric("Avg Speed", f"{avg_spd:.1f} km/h" if avg_spd else "N/A")
        max_spd = activity.get("max_speed")
        c3.metric("Max Speed", f"{max_spd:.1f} km/h" if max_spd else "N/A")

        st.divider()

        if activity.get("total_steps", 0) > 0:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=activity["total_steps"],
                title={"text": "Daily Steps Goal Progress"},
                gauge={
                    "axis": {"range": [0, 10000]},
                    "bar": {"color": "#4fc3f7"},
                    "steps": [
                        {"range": [0, 5000], "color": "#333"},
                        {"range": [5000, 7500], "color": "#444"},
                        {"range": [7500, 10000], "color": "#555"},
                    ],
                    "threshold": {
                        "line": {"color": "#ff6b6b", "width": 4},
                        "thickness": 0.75,
                        "value": 10000,
                    },
                },
            ))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data available.")

with tab_location:
    try:
        loc_data = api.get_location_history(device_id, limit=200)
    except Exception:
        loc_data = {}

    locations = loc_data.get("locations", [])
    if not locations:
        st.info("No location data available.")
    else:
        loc_df = pd.DataFrame(locations)
        loc_df["timestamp"] = pd.to_datetime(loc_df["timestamp"])

        fig = px.scatter_mapbox(
            loc_df, lat="latitude", lon="longitude",
            hover_data=["timestamp", "speed"],
            zoom=10, height=500,
            color_discrete_sequence=["#4fc3f7"],
        )
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        if "speed" in loc_df.columns:
            spd_data = loc_df[["timestamp", "speed"]].dropna()
            if not spd_data.empty:
                fig = px.line(spd_data, x="timestamp", y="speed",
                              title="Speed Over Time",
                              labels={"speed": "km/h", "timestamp": "Time"},
                              color_discrete_sequence=["#66bb6a"])
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

with tab_advanced:
    if df.empty:
        st.info("No telemetry data available.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        st.markdown("### 🔬 Advanced Sensor Data")
        st.caption("Biochemical, Environmental, and Biomechanical telemetry from the IntelliWatch sensors.")

        # Biochemical sensors
        st.markdown("#### 🧪 Biochemical / Sweat Analysis")
        bio_cols = st.columns(3)
        with bio_cols[0]:
            if "cortisol_level" in filtered.columns:
                data = filtered["cortisol_level"].dropna()
                if not data.empty:
                    st.metric("Avg Cortisol", f"{data.mean():.1f} nmol/L")
        with bio_cols[1]:
            if "lactate_level" in filtered.columns:
                data = filtered["lactate_level"].dropna()
                if not data.empty:
                    st.metric("Avg Lactate", f"{data.mean():.2f} mmol/L")
        with bio_cols[2]:
            if "skin_conductance" in filtered.columns:
                data = filtered["skin_conductance"].dropna()
                if not data.empty:
                    st.metric("Avg EDA", f"{data.mean():.2f} uS")

        st.divider()

        # Physiological sensors
        st.markdown("#### 💓 Advanced Physiological")
        phys_cols = st.columns(4)
        with phys_cols[0]:
            if "ecg_value" in filtered.columns:
                data = filtered["ecg_value"].dropna()
                if not data.empty:
                    st.metric("Avg ECG", f"{data.mean():.3f} mV")
        with phys_cols[1]:
            if "hrv_rmssd" in filtered.columns:
                data = filtered["hrv_rmssd"].dropna()
                if not data.empty:
                    st.metric("Avg HRV", f"{data.mean():.1f} ms")
        with phys_cols[2]:
            if "blood_pressure_systolic" in filtered.columns:
                data = filtered["blood_pressure_systolic"].dropna()
                data_d = filtered["blood_pressure_diastolic"].dropna()
                if not data.empty:
                    st.metric("Avg BP", f"{data.mean():.0f}/{data_d.mean():.0f}")
        with phys_cols[3]:
            if "respiration_rate" in filtered.columns:
                data = filtered["respiration_rate"].dropna()
                if not data.empty:
                    st.metric("Avg Resp Rate", f"{data.mean():.0f} bpm")

        st.divider()

        # Environmental sensors
        st.markdown("#### 🌍 Environmental")
        env_cols = st.columns(4)
        with env_cols[0]:
            if "uv_index" in filtered.columns:
                data = filtered["uv_index"].dropna()
                if not data.empty:
                    st.metric("Avg UV Index", f"{data.mean():.1f}")
        with env_cols[1]:
            if "pm25" in filtered.columns:
                data = filtered["pm25"].dropna()
                if not data.empty:
                    st.metric("Avg PM2.5", f"{data.mean():.1f} ug/m3")
        with env_cols[2]:
            if "voc_level" in filtered.columns:
                data = filtered["voc_level"].dropna()
                if not data.empty:
                    st.metric("Avg VOC", f"{data.mean():.0f} ppb")
        with env_cols[3]:
            if "humidity" in filtered.columns:
                data = filtered["humidity"].dropna()
                if not data.empty:
                    st.metric("Avg Humidity", f"{data.mean():.1f}%")

        env_cols2 = st.columns(3)
        with env_cols2[0]:
            if "barometric_pressure" in filtered.columns:
                data = filtered["barometric_pressure"].dropna()
                if not data.empty:
                    st.metric("Avg Pressure", f"{data.mean():.1f} hPa")
        with env_cols2[1]:
            if "ambient_light" in filtered.columns:
                data = filtered["ambient_light"].dropna()
                if not data.empty:
                    st.metric("Avg Light", f"{data.mean():.0f} lux")
        with env_cols2[2]:
            if "ambient_temperature" in filtered.columns:
                data = filtered["ambient_temperature"].dropna()
                if not data.empty:
                    st.metric("Avg Ambient Temp", f"{data.mean():.1f} C")

        st.divider()

        # Biomechanical
        st.markdown("#### 🏃 Biomechanical")
        bio_cols = st.columns(3)
        with bio_cols[0]:
            if "body_orientation" in filtered.columns:
                data = filtered["body_orientation"].dropna()
                if not data.empty:
                    most_common = data.mode()[0] if not data.mode().empty else "N/A"
                    st.metric("Primary Orientation", most_common.title())
        with bio_cols[1]:
            if "gait_symmetry" in filtered.columns:
                data = filtered["gait_symmetry"].dropna()
                if not data.empty:
                    st.metric("Avg Gait Symmetry", f"{data.mean():.3f}")
        with bio_cols[2]:
            if "fall_detected" in filtered.columns:
                data = filtered["fall_detected"].dropna()
                if not data.empty:
                    falls = data.sum()
                    st.metric("Falls Detected", f"{int(falls)}")

        # Time series charts for advanced sensors
        st.divider()
        st.markdown("### 📊 Advanced Sensor Trends")

        advanced_cols = [
            ("cortisol_level", "Cortisol (nmol/L)", "#ff9800"),
            ("lactate_level", "Lactate (mmol/L)", "#ff6b6b"),
            ("skin_conductance", "EDA (uS)", "#e91e63"),
            ("hrv_rmssd", "HRV (ms)", "#4fc3f7"),
            ("uv_index", "UV Index", "#ffd54f"),
            ("pm25", "PM2.5 (ug/m3)", "#ff6b6b"),
            ("voc_level", "VOC (ppb)", "#7c4dff"),
            ("barometric_pressure", "Pressure (hPa)", "#66bb6a"),
        ]

        fig = go.Figure()
        for col, label, color in advanced_cols:
            if col in filtered.columns:
                data = filtered[["timestamp", col]].dropna()
                if not data.empty:
                    fig.add_trace(go.Scatter(
                        x=data["timestamp"], y=data[col],
                        name=label, line=dict(color=color)
                    ))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          title="Multi-Sensor Overlay", height=400)
        st.plotly_chart(fig, use_container_width=True)

with tab_raw:
    if df.empty:
        st.info("No raw data available.")
    else:
        st.dataframe(df, use_container_width=True)
