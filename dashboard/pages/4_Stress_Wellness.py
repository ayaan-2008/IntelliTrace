import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Stress & Wellness - IntelliTrace", page_icon="🧠", layout="wide")
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

st.markdown("# 🧠 Stress & Wellness Dashboard")

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

# === Compute Stress Score (0-100, higher = more stressed) ===
def compute_stress_score(row):
    score = 0.0
    if pd.notna(row.get("hrv_rmssd")):
        hrv = row["hrv_rmssd"]
        if hrv < 20:
            score += 30
        elif hrv < 40:
            score += 15
        elif hrv > 80:
            score -= 10
    if pd.notna(row.get("cortisol_level")):
        cort = row["cortisol_level"]
        if cort > 400:
            score += 25
        elif cort > 250:
            score += 10
        elif cort < 100:
            score -= 5
    if pd.notna(row.get("skin_conductance")):
        eda = row["skin_conductance"]
        if eda > 25:
            score += 25
        elif eda > 15:
            score += 10
        elif eda < 5:
            score -= 5
    if pd.notna(row.get("heart_rate")):
        hr = row["heart_rate"]
        if hr > 100:
            score += 15
        elif hr > 85:
            score += 5
    if pd.notna(row.get("respiration_rate")):
        rr = row["respiration_rate"]
        if rr > 20:
            score += 10
        elif rr < 12:
            score += 5
    return max(0, min(100, score))

if not df.empty:
    df["stress_score"] = df.apply(compute_stress_score, axis=1)

# === Tabs ===
tab_overview, tab_hrv, tab_cortisol, tab_eda, tab_bp = st.tabs(
    ["📊 Overview", "💓 HRV Analysis", "🧪 Cortisol Trends", "⚡ Skin Conductance", "🩺 Blood Pressure"]
)

with tab_overview:
    if df.empty:
        st.info("No telemetry data available yet.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        if filtered.empty:
            st.info(f"No data in the last {days} days.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            if "stress_score" in filtered.columns:
                avg_stress = filtered["stress_score"].mean()
                col1.metric("Avg Stress Score", f"{avg_stress:.0f}/100",
                           delta=None)
                if avg_stress > 50:
                    st.warning("Elevated stress levels detected.")
                elif avg_stress < 20:
                    st.success("Low stress - good relaxation.")

            if "hrv_rmssd" in filtered.columns:
                hrv_data = filtered["hrv_rmssd"].dropna()
                if not hrv_data.empty:
                    col2.metric("Avg HRV (RMSSD)", f"{hrv_data.mean():.1f} ms")

            if "respiration_rate" in filtered.columns:
                rr = filtered["respiration_rate"].dropna()
                if not rr.empty:
                    col3.metric("Avg Respiration", f"{rr.mean():.0f} bpm")

            if "blood_pressure_systolic" in filtered.columns:
                bp = filtered["blood_pressure_systolic"].dropna()
                bp_d = filtered["blood_pressure_diastolic"].dropna()
                if not bp.empty and not bp_d.empty:
                    col4.metric("Blood Pressure", f"{bp.mean():.0f}/{bp_d.mean():.0f}")

            st.divider()

            # Stress score over time
            if "stress_score" in filtered.columns:
                fig = px.area(filtered, x="timestamp", y="stress_score",
                             title="Stress Score Over Time",
                             labels={"stress_score": "Stress (0-100)", "timestamp": "Time"},
                             color_discrete_sequence=["#ff6b6b"])
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                fig.update_yaxes(range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

            # Multi-metric overview
            st.markdown("### Key Wellness Metrics")
            metrics_to_plot = []
            if "hrv_rmssd" in filtered.columns:
                metrics_to_plot.append(("hrv_rmssd", "HRV (ms)", "#4fc3f7"))
            if "cortisol_level" in filtered.columns:
                metrics_to_plot.append(("cortisol_level", "Cortisol (nmol/L)", "#ff9800"))
            if "skin_conductance" in filtered.columns:
                metrics_to_plot.append(("skin_conductance", "EDA (uS)", "#e91e63"))

            if metrics_to_plot:
                fig = go.Figure()
                for col, label, color in metrics_to_plot:
                    data = filtered[["timestamp", col]].dropna()
                    if not data.empty:
                        fig.add_trace(go.Scatter(
                            x=data["timestamp"], y=data[col],
                            name=label, line=dict(color=color)
                        ))
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                  title="Multi-Metric Wellness View")
                st.plotly_chart(fig, use_container_width=True)

with tab_hrv:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        hrv_data = filtered[["timestamp", "hrv_rmssd"]].dropna()
        if hrv_data.empty:
            st.info("No HRV data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Mean HRV", f"{hrv_data['hrv_rmssd'].mean():.1f} ms")
            col2.metric("Min HRV", f"{hrv_data['hrv_rmssd'].min():.1f} ms")
            col3.metric("Max HRV", f"{hrv_data['hrv_rmssd'].max():.1f} ms")

            st.divider()

            fig = px.line(hrv_data, x="timestamp", y="hrv_rmssd",
                         title="Heart Rate Variability (RMSSD) Over Time",
                         labels={"hrv_rmssd": "RMSSD (ms)", "timestamp": "Time"},
                         color_discrete_sequence=["#4fc3f7"])
            fig.add_hline(y=40, line_dash="dash", line_color="green",
                         annotation_text="Healthy threshold")
            fig.add_hline(y=20, line_dash="dash", line_color="red",
                         annotation_text="Low HRV warning")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # HRV distribution
            fig2 = px.histogram(hrv_data, x="hrv_rmssd", nbins=30,
                               title="HRV Distribution",
                               color_discrete_sequence=["#4fc3f7"])
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

with tab_cortisol:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        cort_data = filtered[["timestamp", "cortisol_level"]].dropna()
        if cort_data.empty:
            st.info("No cortisol data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Cortisol", f"{cort_data['cortisol_level'].mean():.1f} nmol/L")
            col2.metric("Peak Cortisol", f"{cort_data['cortisol_level'].max():.1f} nmol/L")
            col3.metric("Min Cortisol", f"{cort_data['cortisol_level'].min():.1f} nmol/L")

            st.divider()

            fig = px.line(cort_data, x="timestamp", y="cortisol_level",
                         title="Cortisol Level Over Time",
                         labels={"cortisol_level": "Cortisol (nmol/L)", "timestamp": "Time"},
                         color_discrete_sequence=["#ff9800"])
            fig.add_hrect(y0=0, y1=100, fillcolor="green", opacity=0.1,
                         annotation_text="Low / Relaxed")
            fig.add_hrect(y0=200, y1=600, fillcolor="red", opacity=0.1,
                         annotation_text="High / Stressed")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Cortisol circadian pattern
            cort_data_copy = cort_data.copy()
            cort_data_copy["hour"] = cort_data_copy["timestamp"].dt.hour
            hourly = cort_data_copy.groupby("hour")["cortisol_level"].mean().reset_index()
            fig2 = px.bar(hourly, x="hour", y="cortisol_level",
                         title="Average Cortisol by Hour of Day (Circadian Pattern)",
                         labels={"cortisol_level": "Avg Cortisol (nmol/L)", "hour": "Hour"},
                         color_discrete_sequence=["#ff9800"])
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

with tab_eda:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        eda_data = filtered[["timestamp", "skin_conductance"]].dropna()
        if eda_data.empty:
            st.info("No EDA data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg EDA", f"{eda_data['skin_conductance'].mean():.2f} uS")
            col2.metric("Peak EDA", f"{eda_data['skin_conductance'].max():.2f} uS")
            col3.metric("Min EDA", f"{eda_data['skin_conductance'].min():.2f} uS")

            st.divider()

            fig = px.line(eda_data, x="timestamp", y="skin_conductance",
                         title="Galvanic Skin Response (EDA) Over Time",
                         labels={"skin_conductance": "EDA (microsiemens)", "timestamp": "Time"},
                         color_discrete_sequence=["#e91e63"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            **What is EDA/GSR?**
            Galvanic Skin Response measures the electrical conductance of your skin, which changes
            with sweat gland activity driven by emotional arousal. Higher EDA = higher stress/excitement.
            """)

with tab_bp:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        bp_data = filtered[["timestamp", "blood_pressure_systolic", "blood_pressure_diastolic"]].dropna()
        if bp_data.empty:
            st.info("No blood pressure data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg BP", f"{bp_data['blood_pressure_systolic'].mean():.0f}/{bp_data['blood_pressure_diastolic'].mean():.0f}")
            col2.metric("Max Systolic", f"{bp_data['blood_pressure_systolic'].max():.0f} mmHg")
            col3.metric("Avg Diastolic", f"{bp_data['blood_pressure_diastolic'].mean():.0f} mmHg")

            st.divider()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=bp_data["timestamp"], y=bp_data["blood_pressure_systolic"],
                name="Systolic", line=dict(color="#ff6b6b")
            ))
            fig.add_trace(go.Scatter(
                x=bp_data["timestamp"], y=bp_data["blood_pressure_diastolic"],
                name="Diastolic", line=dict(color="#4fc3f7")
            ))
            fig.add_hline(y=140, line_dash="dash", line_color="red",
                         annotation_text="High BP threshold (systolic)")
            fig.add_hline(y=90, line_dash="dash", line_color="orange",
                         annotation_text="High BP threshold (diastolic)")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              title="Blood Pressure Over Time",
                              yaxis_title="mmHg")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            **Note:** This is a cuffless blood pressure estimate based on pulse wave analysis.
            For clinical accuracy, use a validated blood pressure monitor.
            """)
