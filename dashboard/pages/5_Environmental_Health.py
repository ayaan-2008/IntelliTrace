import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Environmental Health - IntelliTrace", page_icon="🌍", layout="wide")
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

st.markdown("# 🌍 Environmental Health Dashboard")

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
    history = api.get_telemetry_history(device_id, limit=500)
except Exception:
    history = []

df = pd.DataFrame(history) if history else pd.DataFrame()
if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

tab_uv, tab_air, tab_env, tab_pressure = st.tabs(
    ["☀️ UV Exposure", "💨 Air Quality", "🌡️ Environment", "📊 Pressure & Altitude"]
)

with tab_uv:
    if df.empty:
        st.info("No telemetry data available yet.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        uv_data = filtered[["timestamp", "uv_index"]].dropna()
        if uv_data.empty:
            st.info("No UV data available.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            avg_uv = uv_data["uv_index"].mean()
            max_uv = uv_data["uv_index"].max()
            col1.metric("Avg UV Index", f"{avg_uv:.1f}")
            col2.metric("Peak UV", f"{max_uv:.1f}")

            if max_uv >= 11:
                col3.metric("Risk Level", "Extreme", delta="danger")
            elif max_uv >= 8:
                col3.metric("Risk Level", "Very High", delta="warning")
            elif max_uv >= 6:
                col3.metric("Risk Level", "High")
            elif max_uv >= 3:
                col3.metric("Risk Level", "Moderate")
            else:
                col3.metric("Risk Level", "Low")

            total_uv_dose = (uv_data["uv_index"] * 0.5).sum()
            col4.metric("Est. UV Dose", f"{total_uv_dose:.1f} mJ/cm2")

            st.divider()

            fig = px.line(uv_data, x="timestamp", y="uv_index",
                         title="UV Index Over Time",
                         labels={"uv_index": "UV Index", "timestamp": "Time"},
                         color_discrete_sequence=["#ff9800"])
            fig.add_hrect(y0=0, y1=2, fillcolor="green", opacity=0.1, annotation_text="Low")
            fig.add_hrect(y0=3, y1=5, fillcolor="yellow", opacity=0.1, annotation_text="Moderate")
            fig.add_hrect(y0=6, y1=7, fillcolor="orange", opacity=0.1, annotation_text="High")
            fig.add_hrect(y0=8, y1=11, fillcolor="red", opacity=0.1, annotation_text="Very High")
            fig.add_hrect(y0=11, y1=15, fillcolor="purple", opacity=0.1, annotation_text="Extreme")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # UV by hour of day
            uv_copy = uv_data.copy()
            uv_copy["hour"] = uv_copy["timestamp"].dt.hour
            hourly = uv_copy.groupby("hour")["uv_index"].mean().reset_index()
            fig2 = px.bar(hourly, x="hour", y="uv_index",
                         title="Average UV by Hour of Day",
                         labels={"uv_index": "Avg UV Index", "hour": "Hour"},
                         color_discrete_sequence=["#ff9800"])
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("""
            **UV Index Guide:**
            - **0-2:** Low - Minimal protection needed
            - **3-5:** Moderate - Seek shade during midday
            - **6-7:** High - Protection essential
            - **8-10:** Very High - Extra protection essential
            - **11+:** Extreme - Avoid sun exposure
            """)

with tab_air:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        col1, col2 = st.columns(2)
        with col1:
            pm_data = filtered[["timestamp", "pm25"]].dropna()
            if not pm_data.empty:
                avg_pm = pm_data["pm25"].mean()
                max_pm = pm_data["pm25"].max()
                st.metric("Avg PM2.5", f"{avg_pm:.1f} ug/m3")
                st.metric("Peak PM2.5", f"{max_pm:.1f} ug/m3")

                if avg_pm > 55:
                    st.warning("Unhealthy air quality detected!")
                elif avg_pm > 35:
                    st.info("Moderate air quality.")
                else:
                    st.success("Good air quality.")
            else:
                st.info("No PM2.5 data.")

        with col2:
            voc_data = filtered[["timestamp", "voc_level"]].dropna()
            if not voc_data.empty:
                avg_voc = voc_data["voc_level"].mean()
                max_voc = voc_data["voc_level"].max()
                st.metric("Avg VOC", f"{avg_voc:.0f} ppb")
                st.metric("Peak VOC", f"{max_voc:.0f} ppb")

                if avg_voc > 500:
                    st.warning("High VOC levels - improve ventilation!")
                elif avg_voc > 200:
                    st.info("Moderate VOC levels.")
                else:
                    st.success("Low VOC levels.")
            else:
                st.info("No VOC data.")

        st.divider()

        fig = go.Figure()
        if not pm_data.empty:
            fig.add_trace(go.Scatter(
                x=pm_data["timestamp"], y=pm_data["pm25"],
                name="PM2.5 (ug/m3)", line=dict(color="#ff6b6b")
            ))
        if not voc_data.empty:
            fig.add_trace(go.Scatter(
                x=voc_data["timestamp"], y=voc_data["voc_level"],
                name="VOC (ppb)", line=dict(color="#4fc3f7"), yaxis="y2"
            ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            title="Air Quality: PM2.5 and VOC Levels",
            yaxis=dict(title="PM2.5 (ug/m3)", side="left"),
            yaxis2=dict(title="VOC (ppb)", side="right", overlaying="y"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Air Quality Guide:**
        - **PM2.5:** 0-12 Good | 12-35 Moderate | 35-55 Unhealthy (Sensitive) | 55+ Unhealthy
        - **VOC:** 0-200 Good | 200-500 Moderate | 500+ Poor - ventilate immediately
        """)

with tab_env:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        col1, col2, col3 = st.columns(3)

        temp_data = filtered[["timestamp", "ambient_temperature"]].dropna()
        if not temp_data.empty:
            col1.metric("Avg Temp", f"{temp_data['ambient_temperature'].mean():.1f} C")
            col1.metric("Temp Range",
                       f"{temp_data['ambient_temperature'].min():.1f} - {temp_data['ambient_temperature'].max():.1f} C")

        hum_data = filtered[["timestamp", "humidity"]].dropna()
        if not hum_data.empty:
            col2.metric("Avg Humidity", f"{hum_data['humidity'].mean():.1f}%")

        light_data = filtered[["timestamp", "ambient_light"]].dropna()
        if not light_data.empty:
            col3.metric("Avg Light", f"{light_data['ambient_light'].mean():.0f} lux")
            col3.metric("Peak Light", f"{light_data['ambient_light'].max():.0f} lux")

        st.divider()

        fig = go.Figure()
        if not temp_data.empty:
            fig.add_trace(go.Scatter(
                x=temp_data["timestamp"], y=temp_data["ambient_temperature"],
                name="Temperature (C)", line=dict(color="#ff9800")
            ))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          title="Ambient Temperature Over Time")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        if not hum_data.empty:
            fig2.add_trace(go.Scatter(
                x=hum_data["timestamp"], y=hum_data["humidity"],
                name="Humidity (%)", line=dict(color="#4fc3f7")
            ))
        fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                           title="Humidity Over Time")
        st.plotly_chart(fig2, use_container_width=True)

        if not light_data.empty:
            fig3 = px.area(light_data, x="timestamp", y="ambient_light",
                          title="Ambient Light Levels",
                          labels={"ambient_light": "Light (lux)", "timestamp": "Time"},
                          color_discrete_sequence=["#ffd54f"])
            fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

with tab_pressure:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        baro_data = filtered[["timestamp", "barometric_pressure", "altitude"]].dropna()
        if baro_data.empty:
            st.info("No pressure data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Pressure", f"{baro_data['barometric_pressure'].mean():.1f} hPa")
            col2.metric("Pressure Range",
                       f"{baro_data['barometric_pressure'].min():.1f} - {baro_data['barometric_pressure'].max():.1f} hPa")
            if "altitude" in baro_data.columns:
                alt_data = baro_data["altitude"].dropna()
                if not alt_data.empty:
                    col3.metric("Altitude", f"{alt_data.mean():.0f} m")

            st.divider()

            fig = px.line(baro_data, x="timestamp", y="barometric_pressure",
                         title="Barometric Pressure Over Time",
                         labels={"barometric_pressure": "Pressure (hPa)", "timestamp": "Time"},
                         color_discrete_sequence=["#66bb6a"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Pressure trend as weather indicator
            if len(baro_data) > 10:
                recent = baro_data.tail(20)["barometric_pressure"].mean()
                earlier = baro_data.head(20)["barometric_pressure"].mean()
                diff = recent - earlier
                st.info(f"**Pressure trend:** {'Rising' if diff > 0 else 'Falling'} ({diff:+.1f} hPa) - "
                       f"{'Fair weather expected' if diff > 0 else 'Storm may be approaching'}")

            st.markdown("""
            **Barometric Pressure Guide:**
            - **Above 1020 hPa:** High pressure - Fair, calm weather
            - **1013-1020 hPa:** Normal conditions
            - **Below 1013 hPa:** Low pressure - Cloudy, rain possible
            - **Below 1000 hPa:** Storm conditions likely
            """)
