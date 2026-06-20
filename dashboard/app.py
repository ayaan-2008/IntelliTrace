import streamlit as st

st.set_page_config(
    page_title="IntelliTrace",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #e0e0e0 !important; }
    .stMetric label { color: #a0a0a0 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #4fc3f7 !important; }
</style>
""", unsafe_allow_html=True)

import api_client as api

if "token" not in st.session_state:
    st.session_state.token = None


def show_login():
    st.markdown("# 🛡️ IntelliTrace")
    st.markdown("### Smart Wearable Security & Health Monitoring")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True, type="primary"):
            if email and password:
                try:
                    token = api.login(email, password)
                    st.session_state.token = token
                    st.success("Login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
            else:
                st.warning("Please enter email and password")

    with tab_register:
        reg_email = st.text_input("Email", key="reg_email")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_phone = st.text_input("Phone (optional)", key="reg_phone")
        reg_emergency = st.text_input("Emergency Contact (optional)", key="reg_emergency")
        if st.button("Register", use_container_width=True, key="reg_btn"):
            if reg_email and reg_name and reg_pass:
                try:
                    api.register(reg_email, reg_name, reg_pass, reg_phone, reg_emergency)
                    token = api.login(reg_email, reg_pass)
                    st.session_state.token = token
                    st.success("Account created! Redirecting...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration failed: {e}")
            else:
                st.warning("Please fill in required fields")


def show_dashboard():
    for key in list(st.session_state.keys()):
        if key.startswith("_cache_status_"):
            del st.session_state[key]

    try:
        user = api.get_me()
    except Exception:
        st.session_state.token = None
        st.rerun()
        return

    st.sidebar.markdown(f"**Welcome,** {user['full_name']}")
    st.sidebar.markdown(f"📧 {user['email']}")
    st.sidebar.divider()

    if st.sidebar.button("Logout"):
        st.session_state.token = None
        api._clear_cache()
        st.rerun()

    st.markdown("# 🛡️ IntelliTrace Dashboard")
    st.markdown(f"Welcome back, **{user['full_name']}**!")
    st.divider()

    try:
        devices = api.list_devices()
    except Exception:
        devices = []

    try:
        active_alerts = api.get_active_alerts()
    except Exception:
        active_alerts = []

    online_count = 0
    statuses = {}
    if devices:
        for dev in devices:
            try:
                status = api.get_device_status(dev["id"])
                statuses[dev["id"]] = status
                if status.get("is_online"):
                    online_count += 1
            except Exception:
                statuses[dev["id"]] = {"is_online": False}

    api_ok = True
    try:
        import httpx
        health_r = httpx.get(api.API_BASE.replace("/api/v1", "/health"), timeout=3)
        api_ok = health_r.status_code == 200
    except Exception:
        api_ok = False

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Devices", len(devices))
    with col2:
        st.metric("Active Devices", online_count)
    with col3:
        st.metric("Active Alerts", len(active_alerts))
    with col4:
        st.metric("System Status", "🟢 Online" if api_ok else "🔴 Offline")

    st.divider()

    if not devices:
        st.info("No devices paired yet. Go to **Devices** page to pair a wearable.")
    else:
        st.markdown("### 📊 Device Overview")

        for dev in devices:
            is_online = statuses.get(dev["id"], {}).get("is_online", False)
            badge = "🟢 Online" if is_online else "🔴 Offline"

            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.markdown(f"**{dev['device_name']}**")
                c2.markdown(badge)
                if dev.get("firmware_version"):
                    c3.markdown(f"FW: {dev['firmware_version']}")
                last = dev.get("last_seen", "Never")
                c4.markdown(f"Last seen: {last[:19] if last and last != 'Never' else 'Never'}")

    st.divider()
    st.markdown("### 🚀 Quick Navigation")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        if st.button("📱 Devices", use_container_width=True):
            st.switch_page("pages/1_Devices.py")
    with mc2:
        if st.button("📈 Telemetry", use_container_width=True):
            st.switch_page("pages/2_Telemetry.py")
    with mc3:
        if st.button("🚨 Alerts", use_container_width=True):
            st.switch_page("pages/3_Alerts.py")


if st.session_state.token:
    show_dashboard()
else:
    show_login()
