import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Muscle & Recovery - IntelliTrace", page_icon="💪", layout="wide")
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

st.markdown("# 💪 Muscle & Recovery Dashboard")

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


def compute_recovery_score(row):
    """Compute recovery score 0-100 based on multiple metrics."""
    score = 50.0
    hrv = row.get("hrv_rmssd")
    hr = row.get("heart_rate")
    resp = row.get("respiration_rate")
    lactate = row.get("lactate_level")
    cortisol = row.get("cortisol_level")
    sleep_quality = row.get("hrv_rmssd", 50)

    if pd.notna(hrv):
        if hrv > 60:
            score += 15
        elif hrv > 40:
            score += 8
        elif hrv < 20:
            score -= 15

    if pd.notna(hr) and hr < 70:
        score += 10
    elif pd.notna(hr) and hr > 100:
        score -= 10

    if pd.notna(resp) and 12 <= resp <= 18:
        score += 5

    if pd.notna(lactate):
        if lactate < 2.0:
            score += 10
        elif lactate > 5.0:
            score -= 10

    if pd.notna(cortisol) and cortisol < 200:
        score += 5
    elif pd.notna(cortisol) and cortisol > 400:
        score -= 10

    return round(max(0, min(100, score)), 1)


tab_overview, tab_lactate, tab_gait, tab_recovery = st.tabs(
    ["📊 Overview", "🧪 Lactate & Activity", "🏃 Gait Analysis", "🔄 Recovery Score"]
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

            if "lactate_level" in filtered.columns:
                lact = filtered["lactate_level"].dropna()
                if not lact.empty:
                    col1.metric("Avg Lactate", f"{lact.mean():.2f} mmol/L")
                    col2.metric("Peak Lactate", f"{lact.max():.2f} mmol/L")

            if "gait_symmetry" in filtered.columns:
                gait = filtered["gait_symmetry"].dropna()
                if not gait.empty:
                    col3.metric("Avg Gait Symmetry", f"{gait.mean():.3f}")
                    if gait.mean() < 0.9:
                        st.warning("Gait asymmetry detected - possible injury risk.")

            if "body_orientation" in filtered.columns:
                orientations = filtered["body_orientation"].dropna().value_counts()
                most_common = orientations.index[0] if not orientations.empty else "N/A"
                col4.metric("Most Common", most_common.title())

            st.divider()

            # Activity breakdown
            if "body_orientation" in filtered.columns:
                st.markdown("### Activity Distribution")
                orient_counts = filtered["body_orientation"].value_counts().reset_index()
                orient_counts.columns = ["orientation", "count"]

                fig = px.pie(orient_counts, values="count", names="orientation",
                            title="Activity Breakdown",
                            color_discrete_map={
                                "standing": "#4fc3f7",
                                "sitting": "#7c4dff",
                                "lying": "#1a1a2e",
                                "walking": "#66bb6a",
                                "running": "#ff6b6b",
                            })
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            # Steps and activity metrics
            if "steps" in filtered.columns:
                st.markdown("### Activity Metrics")
                steps_data = filtered[["timestamp", "steps"]].dropna()
                if not steps_data.empty:
                    c1, c2, c3 = st.columns(3)
                    total_steps = steps_data["steps"].sum()
                    c1.metric("Total Steps", f"{total_steps:,}")
                    avg_steps = steps_data["steps"].mean()
                    c2.metric("Avg Steps/Reading", f"{avg_steps:.0f}")
                    c3.metric("Activity Readings", f"{len(steps_data)}")

with tab_lactate:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        lact_data = filtered[["timestamp", "lactate_level", "heart_rate", "steps"]].dropna(subset=["lactate_level"])
        if lact_data.empty:
            st.info("No lactate data available.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Lactate", f"{lact_data['lactate_level'].mean():.2f} mmol/L")
            col2.metric("Peak Lactate", f"{lact_data['lactate_level'].max():.2f} mmol/L")
            col3.metric("Resting Lactate", f"{lact_data['lactate_level'].min():.2f} mmol/L")

            st.divider()

            fig = px.line(lact_data, x="timestamp", y="lactate_level",
                         title="Blood Lactate Level Over Time",
                         labels={"lactate_level": "Lactate (mmol/L)", "timestamp": "Time"},
                         color_discrete_sequence=["#ff6b6b"])
            fig.add_hrect(y0=0, y1=2, fillcolor="green", opacity=0.1, annotation_text="Resting")
            fig.add_hrect(y0=2, y1=4, fillcolor="yellow", opacity=0.1, annotation_text="Light Activity")
            fig.add_hrect(y0=4, y1=8, fillcolor="orange", opacity=0.1, annotation_text="Moderate")
            fig.add_hrect(y0=8, y1=20, fillcolor="red", opacity=0.1, annotation_text="Intense / Anaerobic")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Lactate vs Heart Rate correlation
            lr_data = lact_data[["heart_rate", "lactate_level"]].dropna()
            if not lr_data.empty and len(lr_data) > 5:
                fig2 = px.scatter(lr_data, x="heart_rate", y="lactate_level",
                                 title="Lactate vs Heart Rate (Performance Curve)",
                                 labels={"heart_rate": "Heart Rate (bpm)", "lactate_level": "Lactate (mmol/L)"},
                                 color_discrete_sequence=["#ff6b6b"])
                fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("""
            **Lactate Levels Guide:**
            - **< 2.0 mmol/L:** Resting / recovery zone
            - **2-4 mmol/L:** Aerobic / endurance zone
            - **4-8 mmol/L:** Lactate threshold zone (training zone)
            - **> 8 mmol/L:** Anaerobic / high-intensity zone
            - Lactate clearance rate is an indicator of fitness level
            """)

with tab_gait:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff]

        gait_data = filtered[["timestamp", "gait_symmetry", "accel_x", "accel_y", "accel_z",
                              "body_orientation", "speed"]].dropna(subset=["gait_symmetry"])
        if gait_data.empty:
            st.info("No gait data available (device may not be moving).")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Gait Symmetry", f"{gait_data['gait_symmetry'].mean():.3f}")
            col2.metric("Min Symmetry", f"{gait_data['gait_symmetry'].min():.3f}")

            sym_score = gait_data["gait_symmetry"].mean()
            if sym_score > 0.95:
                col3.metric("Status", "Excellent", delta="normal")
            elif sym_score > 0.9:
                col3.metric("Status", "Good")
            elif sym_score > 0.85:
                col3.metric("Status", "Fair", delta="monitor")
            else:
                col3.metric("Status", "Poor", delta="concern")

            st.divider()

            fig = px.line(gait_data, x="timestamp", y="gait_symmetry",
                         title="Gait Symmetry Over Time",
                         labels={"gait_symmetry": "Symmetry (0-1)", "timestamp": "Time"},
                         color_discrete_sequence=["#66bb6a"])
            fig.add_hline(y=0.95, line_dash="dash", line_color="green", annotation_text="Excellent")
            fig.add_hline(y=0.9, line_dash="dash", line_color="yellow", annotation_text="Good")
            fig.add_hline(y=0.85, line_dash="dash", line_color="red", annotation_text="Concern")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Accelerometer magnitude during movement
            if "accel_x" in gait_data.columns:
                gait_copy = gait_data.copy()
                gait_copy["accel_mag"] = np.sqrt(
                    gait_copy["accel_x"]**2 + gait_copy["accel_y"]**2 + gait_copy["accel_z"]**2
                )
                fig2 = px.line(gait_copy, x="timestamp", y="accel_mag",
                              title="Movement Intensity (Accelerometer Magnitude)",
                              labels={"accel_mag": "Magnitude (g)", "timestamp": "Time"},
                              color_discrete_sequence=["#4fc3f7"])
                fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

            # Speed during movement
            speed_data = gait_data[["timestamp", "speed"]].dropna()
            if not speed_data.empty:
                fig3 = px.line(speed_data, x="timestamp", y="speed",
                              title="Speed During Activity",
                              labels={"speed": "Speed (km/h)", "timestamp": "Time"},
                              color_discrete_sequence=["#ff9800"])
                fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig3, use_container_width=True)

            st.markdown("""
            **Gait Analysis Guide:**
            - **Symmetry > 0.95:** Excellent - balanced movement
            - **Symmetry 0.9-0.95:** Good - minor imbalance
            - **Symmetry < 0.9:** Fair to Poor - possible injury or fatigue
            - Asymmetry may indicate: muscle imbalance, joint issue, fatigue, or injury risk
            """)

with tab_recovery:
    if df.empty:
        st.info("No data.")
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = df[df["timestamp"] >= cutoff].copy()

        if filtered.empty:
            st.info(f"No data in the last {days} days.")
        else:
            filtered["recovery_score"] = filtered.apply(compute_recovery_score, axis=1)

            col1, col2, col3, col4 = st.columns(4)

            avg_recovery = filtered["recovery_score"].mean()
            latest_recovery = filtered["recovery_score"].iloc[-1]

            col1.metric("Current Recovery", f"{latest_recovery:.0f}/100")
            col2.metric("Avg Recovery", f"{avg_recovery:.0f}/100")

            if latest_recovery > 70:
                col3.metric("Status", "Well Recovered", delta="green")
            elif latest_recovery > 40:
                col3.metric("Status", "Moderate Recovery")
            else:
                col3.metric("Status", "Needs Recovery", delta="red")

            # Recovery trend
            col4.metric("Trend",
                        "Improving" if len(filtered) > 1 and filtered["recovery_score"].tail(5).mean() > filtered["recovery_score"].head(5).mean() else "Stable")

            st.divider()

            fig = px.area(filtered, x="timestamp", y="recovery_score",
                         title="Recovery Score Over Time",
                         labels={"recovery_score": "Recovery (0-100)", "timestamp": "Time"},
                         color_discrete_sequence=["#66bb6a"])
            fig.update_yaxes(range=[0, 100])
            fig.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Well Recovered")
            fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Needs Recovery")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Recovery components breakdown
            st.markdown("### Recovery Components")

            metrics_available = []
            if "hrv_rmssd" in filtered.columns:
                hrv = filtered["hrv_rmssd"].dropna()
                if not hrv.empty:
                    metrics_available.append(("HRV", hrv.mean(), "ms", "Higher = Better Recovery"))

            if "cortisol_level" in filtered.columns:
                cort = filtered["cortisol_level"].dropna()
                if not cort.empty:
                    metrics_available.append(("Cortisol", cort.mean(), "nmol/L", "Lower = Better Recovery"))

            if "lactate_level" in filtered.columns:
                lact = filtered["lactate_level"].dropna()
                if not lact.empty:
                    metrics_available.append(("Lactate", lact.mean(), "mmol/L", "Lower = Recovered"))

            if "heart_rate" in filtered.columns:
                hr = filtered["heart_rate"].dropna()
                if not hr.empty:
                    metrics_available.append(("Resting HR", hr.mean(), "bpm", "Lower = Better Fitness"))

            if metrics_available:
                cols = st.columns(len(metrics_available))
                for i, (name, val, unit, hint) in enumerate(metrics_available):
                    cols[i].metric(f"Avg {name}", f"{val:.1f} {unit}", help=hint)

            # Recovery recommendations
            st.divider()
            st.markdown("### Recovery Recommendations")

            if latest_recovery > 70:
                st.success("**You are well recovered!** Ready for intense training or activity.")
            elif latest_recovery > 40:
                st.info("**Moderate recovery.** Consider light activity and good nutrition.")
            else:
                st.warning("**Recovery needed.** Prioritize rest, hydration, and sleep.")

            recommendations = []
            if "hrv_rmssd" in filtered.columns:
                hrv_latest = filtered["hrv_rmssd"].iloc[-1] if not filtered["hrv_rmssd"].dropna().empty else 40
                if hrv_latest < 30:
                    recommendations.append("- Low HRV detected. Consider meditation or deep breathing exercises.")
            if "sleep_quality" not in filtered.columns and "hrv_rmssd" in filtered.columns:
                recommendations.append("- Monitor sleep patterns for recovery optimization.")
            if "lactate_level" in filtered.columns:
                lact_latest = filtered["lactate_level"].iloc[-1] if not filtered["lactate_level"].dropna().empty else 1.0
                if lact_latest > 4:
                    recommendations.append("- Elevated lactate. Light cool-down activity may help clear lactate.")
            if not recommendations:
                recommendations.append("- Maintain consistent sleep schedule.")
                recommendations.append("- Stay hydrated throughout the day.")
                recommendations.append("- Include rest days in your training schedule.")

            for rec in recommendations:
                st.markdown(rec)
