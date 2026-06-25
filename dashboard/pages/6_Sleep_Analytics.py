import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Sleep Analytics - IntelliTrace", page_icon="😴", layout="wide")
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

st.markdown("# 😴 Sleep Analytics Dashboard")

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

days = st.slider("Time Range (nights)", 1, 30, 7)

try:
    history = api.get_telemetry_history(device_id, limit=1000)
except Exception:
    history = []

df = pd.DataFrame(history) if history else pd.DataFrame()
if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date


def classify_sleep_stage(row):
    """Simple sleep stage classifier based on sensor data."""
    hr = row.get("heart_rate", 70)
    accel_mag = 0
    if pd.notna(row.get("accel_x")) and pd.notna(row.get("accel_y")) and pd.notna(row.get("accel_z")):
        accel_mag = abs(row["accel_x"]) + abs(row["accel_y"]) + abs(row["accel_z"])
    orientation = row.get("body_orientation", "standing")
    hrv = row.get("hrv_rmssd", 40) or 40
    resp = row.get("respiration_rate", 16) or 16

    if orientation == "lying":
        if accel_mag > 1.5 or resp > 20:
            return "awake"
        elif hrv > 60 and resp < 13:
            return "deep"
        elif hrv > 35 and resp < 16:
            return "light"
        else:
            return "rem"
    return "awake"


def compute_sleep_quality(night_df):
    """Compute a sleep quality score 0-100."""
    if night_df.empty:
        return 0

    stages = night_df.apply(classify_sleep_stage, axis=1)
    sleep_pct = (stages != "awake").mean() * 100
    deep_pct = (stages == "deep").mean() * 100
    rem_pct = (stages == "rem").mean() * 100

    hrv_vals = night_df["hrv_rmssd"].dropna()
    avg_hrv = hrv_vals.mean() if not hrv_vals.empty else 40

    score = 0
    score += min(40, sleep_pct * 0.5)
    score += min(25, deep_pct * 1.5)
    score += min(20, rem_pct * 1.0)
    score += min(15, avg_hrv * 0.2)

    return round(max(0, min(100, score)), 1)


tab_overview, tab_stages, tab_trends, tab_circadian = st.tabs(
    ["📊 Sleep Overview", "🌙 Sleep Stages", "📈 Trends", "⏰ Circadian Rhythm"]
)

with tab_overview:
    if df.empty:
        st.info("No telemetry data available yet.")
    else:
        # Filter nighttime data (10 PM - 8 AM)
        night_hours = list(range(22, 24)) + list(range(0, 8))
        night_df = df[df["hour"].isin(night_hours)].copy()

        if night_df.empty:
            st.info("No nighttime data found.")
        else:
            st.markdown("### Last Night's Sleep Summary")

            # Use the most recent night's data
            latest_date = night_df["date"].max()
            last_night = night_df[night_df["date"] == latest_date]

            if not last_night.empty:
                stages = last_night.apply(classify_sleep_stage, axis=1)
                total_readings = len(last_night)
                sleep_readings = (stages != "awake").sum()

                sleep_duration_hours = (sleep_readings / total_readings) * 10 if total_readings > 0 else 0

                quality = compute_sleep_quality(last_night)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Sleep Quality", f"{quality}/100")
                col2.metric("Est. Duration", f"{sleep_duration_hours:.1f} hrs")

                deep_pct = (stages == "deep").mean() * 100
                rem_pct = (stages == "rem").mean() * 100
                light_pct = (stages == "light").mean() * 100

                col3.metric("Deep Sleep", f"{deep_pct:.0f}%")
                col4.metric("REM Sleep", f"{rem_pct:.0f}%")

                st.divider()

                # Stage breakdown pie chart
                stage_counts = stages.value_counts()
                fig = go.Figure(go.Pie(
                    labels=stage_counts.index,
                    values=stage_counts.values,
                    marker=dict(colors=["#1a1a2e", "#4fc3f7", "#7c4dff", "#ff6b6b"]),
                    hole=0.3
                ))
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                  title="Sleep Stage Distribution")
                st.plotly_chart(fig, use_container_width=True)

                # Key metrics
                st.markdown("### Key Sleep Metrics")
                c1, c2, c3, c4 = st.columns(4)

                hr_sleep = last_night["heart_rate"].dropna()
                if not hr_sleep.empty:
                    c1.metric("Avg Heart Rate", f"{hr_sleep.mean():.0f} bpm",
                             help="Lower is usually better during sleep")

                hrv_sleep = last_night["hrv_rmssd"].dropna()
                if not hrv_sleep.empty:
                    c2.metric("Avg HRV", f"{hrv_sleep.mean():.1f} ms",
                             help="Higher HRV during sleep = better recovery")

                rr_sleep = last_night["respiration_rate"].dropna()
                if not rr_sleep.empty:
                    c3.metric("Avg Respiration", f"{rr_sleep.mean():.0f} bpm")

                spo2_sleep = last_night["sp_o2"].dropna()
                if not spo2_sleep.empty:
                    c4.metric("Avg SpO2", f"{spo2_sleep.mean():.0f}%",
                             help="Should stay above 94% during sleep")

with tab_stages:
    if df.empty:
        st.info("No data.")
    else:
        night_hours = list(range(22, 24)) + list(range(0, 8))
        night_df = df[df["hour"].isin(night_hours)].copy()

        if night_df.empty:
            st.info("No nighttime data found.")
        else:
            st.markdown("### Sleep Stage Timeline")

            latest_date = night_df["date"].max()
            last_night = night_df[night_df["date"] == latest_date]

            if not last_night.empty:
                last_night = last_night.copy()
                last_night["sleep_stage"] = last_night.apply(classify_sleep_stage, axis=1)

                stage_map = {"awake": 0, "light": 1, "deep": 2, "rem": 3}
                last_night["stage_num"] = last_night["sleep_stage"].map(stage_map)

                fig = px.scatter(last_night, x="timestamp", y="stage_num",
                               color="sleep_stage",
                               color_discrete_map={"awake": "#ff6b6b", "light": "#4fc3f7",
                                                   "deep": "#7c4dff", "rem": "#ff9800"},
                               title="Sleep Stages Throughout the Night",
                               labels={"stage_num": "Stage", "timestamp": "Time"})
                fig.update_yaxes(
                    tickvals=[0, 1, 2, 3],
                    ticktext=["Awake", "Light", "Deep", "REM"]
                )
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                # Heart rate during sleep
                hr_data = last_night[["timestamp", "heart_rate"]].dropna()
                if not hr_data.empty:
                    fig2 = px.line(hr_data, x="timestamp", y="heart_rate",
                                  title="Heart Rate During Sleep",
                                  color_discrete_sequence=["#ff6b6b"])
                    fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig2, use_container_width=True)

                # HRV during sleep
                hrv_data = last_night[["timestamp", "hrv_rmssd"]].dropna()
                if not hrv_data.empty:
                    fig3 = px.line(hrv_data, x="timestamp", y="hrv_rmssd",
                                  title="HRV During Sleep",
                                  color_discrete_sequence=["#4fc3f7"])
                    fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig3, use_container_width=True)

with tab_trends:
    if df.empty:
        st.info("No data.")
    else:
        night_hours = list(range(22, 24)) + list(range(0, 8))
        night_df = df[df["hour"].isin(night_hours)].copy()

        if night_df.empty:
            st.info("No nighttime data found.")
        else:
            # Compute nightly metrics
            nightly_stats = []
            for date_val, group in night_df.groupby("date"):
                quality = compute_sleep_quality(group)
                stages = group.apply(classify_sleep_stage, axis=1)
                deep_pct = (stages == "deep").mean() * 100
                rem_pct = (stages == "rem").mean() * 100
                light_pct = (stages == "light").mean() * 100
                avg_hrv = group["hrv_rmssd"].dropna().mean() if not group["hrv_rmssd"].dropna().empty else None
                avg_hr = group["heart_rate"].dropna().mean() if not group["heart_rate"].dropna().empty else None
                avg_spo2 = group["sp_o2"].dropna().mean() if not group["sp_o2"].dropna().empty else None

                nightly_stats.append({
                    "date": date_val,
                    "quality": quality,
                    "deep_pct": deep_pct,
                    "rem_pct": rem_pct,
                    "light_pct": light_pct,
                    "avg_hrv": avg_hrv,
                    "avg_hr": avg_hr,
                    "avg_spo2": avg_spo2,
                })

            trends_df = pd.DataFrame(nightly_stats)

            if not trends_df.empty:
                st.markdown("### Sleep Quality Trend")
                fig = px.line(trends_df, x="date", y="quality",
                             title="Sleep Quality Over Time",
                             labels={"quality": "Quality Score", "date": "Night"},
                             color_discrete_sequence=["#7c4dff"])
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Deep & REM Sleep Trend")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=trends_df["date"], y=trends_df["deep_pct"],
                                         name="Deep %", line=dict(color="#7c4dff")))
                fig2.add_trace(go.Scatter(x=trends_df["date"], y=trends_df["rem_pct"],
                                         name="REM %", line=dict(color="#ff9800")))
                fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                  title="Deep vs REM Sleep Percentage")
                st.plotly_chart(fig2, use_container_width=True)

                # Average nightly HRV trend
                hrv_trend = trends_df[["date", "avg_hrv"]].dropna()
                if not hrv_trend.empty:
                    st.markdown("### Nightly HRV Trend (Recovery Indicator)")
                    fig3 = px.line(hrv_trend, x="date", y="avg_hrv",
                                  title="Average HRV During Sleep",
                                  labels={"avg_hrv": "HRV (ms)", "date": "Night"},
                                  color_discrete_sequence=["#4fc3f7"])
                    fig3.add_hline(y=50, line_dash="dash", line_color="green",
                                  annotation_text="Good recovery")
                    fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig3, use_container_width=True)

with tab_circadian:
    if df.empty:
        st.info("No data.")
    else:
        st.markdown("### Circadian Rhythm Analysis")

        # Heart rate pattern by hour
        hr_by_hour = df.groupby("hour")["heart_rate"].mean().reset_index()
        hr_by_hour.columns = ["hour", "avg_hr"]

        fig = px.line(hr_by_hour, x="hour", y="avg_hr",
                     title="Average Heart Rate by Hour of Day (Circadian Pattern)",
                     labels={"avg_hr": "Heart Rate (bpm)", "hour": "Hour of Day"},
                     color_discrete_sequence=["#ff6b6b"])
        fig.update_xaxes(dtick=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        # Cortisol circadian pattern
        cort_by_hour = df.groupby("hour")["cortisol_level"].mean().reset_index()
        cort_by_hour.columns = ["hour", "avg_cortisol"]
        cort_by_hour = cort_by_hour.dropna()

        if not cort_by_hour.empty:
            fig2 = px.bar(cort_by_hour, x="hour", y="avg_cortisol",
                         title="Cortisol Circadian Rhythm",
                         labels={"avg_cortisol": "Cortisol (nmol/L)", "hour": "Hour of Day"},
                         color_discrete_sequence=["#ff9800"])
            fig2.update_xaxes(dtick=1)
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("""
            **Cortisol Rhythm:**
            - **Peak (6-8 AM):** Cortisol peaks to help wake you up
            - **Decline (afternoon):** Gradual decline throughout the day
            - **Nadir (midnight-2 AM):** Lowest point, deepest sleep
            - A disrupted pattern may indicate chronic stress or sleep disorders
            """)

        # Skin temperature overnight pattern
        if "skin_temperature" in df.columns:
            temp_by_hour = df.groupby("hour")["skin_temperature"].mean().reset_index()
            fig3 = px.line(temp_by_hour, x="hour", y="skin_temperature",
                          title="Skin Temperature Circadian Pattern",
                          labels={"skin_temperature": "Temperature (C)", "hour": "Hour"},
                          color_discrete_sequence=["#ffa726"])
            fig3.update_xaxes(dtick=1)
            fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("""
        **About Circadian Rhythm:**
        Your body follows a ~24-hour cycle regulating sleep, temperature, hormones, and vital signs.
        - Heart rate drops during sleep and rises before waking
        - Cortisol peaks in the morning and falls at night
        - Skin temperature drops in the evening (signal for sleep onset)
        - Disrupted rhythms correlate with poor sleep quality and health issues
        """)
