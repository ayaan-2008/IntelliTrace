import streamlit as st

st.set_page_config(page_title="Alerts - IntelliTrace", page_icon="🚨", layout="wide")
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

st.markdown("# 🚨 Alerts & Notifications")

tab_active, tab_all = st.tabs(["Active Alerts", "All Alerts"])

SEVERITY_COLORS = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "CRITICAL": "🔴",
}

ALERT_ICONS = {
    "UNAUTHORIZED_WEARER": "👤",
    "DEVICE_NOT_WORN": "📵",
    "UNUSUAL_LOCATION": "📍",
    "HEALTH_ANOMALY": "❤️‍🩹",
    "BATTERY_CRITICAL": "🪫",
}

with tab_active:
    try:
        active = api.get_active_alerts()
    except Exception as e:
        st.error(f"Failed to load alerts: {e}")
        active = []

    if not active:
        st.success("No active alerts. All clear!")
    else:
        st.metric("Active Alerts", len(active))
        st.divider()

        for alert in active:
            sev = alert.get("severity", "LOW")
            icon = ALERT_ICONS.get(alert.get("alert_type", ""), "⚠️")
            sev_icon = SEVERITY_COLORS.get(sev, "⚪")

            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"### {icon} {alert.get('alert_type', 'Unknown').replace('_', ' ').title()}")
                    st.markdown(alert.get("message", "No message"))
                    st.caption(f"Device: `{alert.get('device_id', 'N/A')[:8]}...` | {alert.get('created_at', 'N/A')[:19]}")
                with c2:
                    st.markdown(f"**Severity:** {sev_icon} {sev}")
                with c3:
                    if st.button("Resolve", key=f"resolve_{alert['id']}", type="primary"):
                        try:
                            api.resolve_alert(alert["id"])
                            st.success("Alert resolved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

                if alert.get("latitude") and alert.get("longitude"):
                    st.caption(f"📍 Location: ({alert['latitude']:.4f}, {alert['longitude']:.4f})")

                st.divider()

with tab_all:
    try:
        all_alerts = api.list_alerts(limit=100)
    except Exception as e:
        st.error(f"Failed to load alerts: {e}")
        all_alerts = []

    if not all_alerts:
        st.info("No alerts found.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        resolved_count = sum(1 for a in all_alerts if a.get("is_resolved"))
        unresolved_count = len(all_alerts) - resolved_count
        col1.metric("Total", len(all_alerts))
        col2.metric("Resolved", resolved_count)
        col3.metric("Unresolved", unresolved_count)
        if all_alerts:
            types = {}
            for a in all_alerts:
                t = a.get("alert_type", "Unknown")
                types[t] = types.get(t, 0) + 1
            most_common = max(types, key=types.get)
            col4.metric("Most Common", most_common.replace("_", " ").title())

        st.divider()

        filter_type = st.selectbox("Filter by Type", ["All"] + list(set(a.get("alert_type", "") for a in all_alerts)))
        filter_sev = st.selectbox("Filter by Severity", ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

        filtered = all_alerts
        if filter_type != "All":
            filtered = [a for a in filtered if a.get("alert_type") == filter_type]
        if filter_sev != "All":
            filtered = [a for a in filtered if a.get("severity") == filter_sev]

        for alert in filtered:
            sev = alert.get("severity", "LOW")
            icon = ALERT_ICONS.get(alert.get("alert_type", ""), "⚠️")
            sev_icon = SEVERITY_COLORS.get(sev, "⚪")
            resolved_badge = "✅" if alert.get("is_resolved") else "❌"

            with st.expander(f"{resolved_badge} {icon} {alert.get('alert_type', '').replace('_', ' ').title()} — {sev_icon} {sev}"):
                st.markdown(f"**Message:** {alert.get('message', 'N/A')}")
                st.markdown(f"**Device:** `{alert.get('device_id', 'N/A')[:8]}...`")
                st.markdown(f"**Created:** {alert.get('created_at', 'N/A')[:19]}")
                if alert.get("resolved_at"):
                    st.markdown(f"**Resolved:** {alert['resolved_at'][:19]}")
                if alert.get("latitude") and alert.get("longitude"):
                    st.markdown(f"**Location:** ({alert['latitude']:.4f}, {alert['longitude']:.4f})")
                if not alert.get("is_resolved"):
                    if st.button("Resolve", key=f"resolve_all_{alert['id']}"):
                        try:
                            api.resolve_alert(alert["id"])
                            st.success("Resolved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")
