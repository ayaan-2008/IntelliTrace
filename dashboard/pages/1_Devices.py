import streamlit as st

st.set_page_config(page_title="Devices - IntelliTrace", page_icon="📱", layout="wide")
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

st.markdown("# 📱 Device Management")

tab_list, tab_pair = st.tabs(["My Devices", "Pair New Device"])

with tab_list:
    try:
        devices = api.list_devices()
    except Exception as e:
        st.error(f"Failed to load devices: {e}")
        devices = []

    if not devices:
        st.info("No devices paired. Go to **Pair New Device** tab.")
    else:
        for dev in devices:
            try:
                status = api.get_device_status(dev["id"])
                is_online = status.get("is_online", False)
                battery = status.get("battery_level")
            except Exception:
                is_online = False
                battery = None

            with st.expander(f"{'🟢' if is_online else '🔴'} {dev['device_name']} — {dev['device_serial']}", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Status", "Online" if is_online else "Offline")
                c2.metric("Battery", f"{battery}%" if battery else "N/A")
                c3.metric("Firmware", dev.get("firmware_version") or "N/A")
                last = dev.get("last_seen")
                c4.metric("Last Seen", last[:19] if last else "Never")

                st.markdown(f"**Paired:** {dev.get('paired_at', 'N/A')[:19] if dev.get('paired_at') else 'N/A'}")

                if st.button(f"Unpair {dev['device_name']}", key=f"unpair_{dev['id']}", type="secondary"):
                    try:
                        api.unpair_device(dev["id"])
                        st.success(f"Device {dev['device_name']} unpaired.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to unpair: {e}")

with tab_pair:
    st.markdown("### Pair a New Wearable Device")
    serial = st.text_input("Device Serial Number", placeholder="e.g. IW-ABC12345")
    if st.button("Pair Device", type="primary"):
        if serial:
            try:
                result = api.pair_device(serial)
                st.success(f"Device paired! ID: {result['device_id']}")
                st.code(f"API Key: {result['api_key']}", language=None)
                st.info("Save this API key — it's needed for telemetry ingestion.")
                st.rerun()
            except Exception as e:
                st.error(f"Pairing failed: {e}")
        else:
            st.warning("Enter a device serial number.")
