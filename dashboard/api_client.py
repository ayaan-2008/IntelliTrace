import os
import time

import httpx
import streamlit as st

API_BASE = os.environ.get("INTELLITRACE_API_URL", "http://localhost:8000/api/v1")


def _get_client() -> httpx.Client:
    if "_http_client" not in st.session_state or st.session_state._http_client.is_closed:
        st.session_state._http_client = httpx.Client(base_url=API_BASE, timeout=10.0)
    return st.session_state._http_client


def get_token() -> str | None:
    return st.session_state.get("token")


def _headers() -> dict:
    token = get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_error(e: httpx.HTTPStatusError):
    if e.response.status_code == 401:
        st.session_state.token = None
        st.rerun()
    detail = _extract_detail(e.response)
    raise RuntimeError(detail) from e


def _extract_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if "detail" in body:
            detail = body["detail"]
            if isinstance(detail, list):
                msgs = []
                for item in detail:
                    loc = item.get("loc", [])
                    msg = item.get("msg", "")
                    field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else "input"
                    msgs.append(f"{field}: {msg}")
                return "; ".join(msgs)
            return str(detail)
        return response.text
    except Exception:
        return f"HTTP {response.status_code}"


def _clear_cache():
    for fn_name in ["list_devices", "get_device_status", "get_active_alerts",
                     "get_telemetry_history", "get_health_summary",
                     "get_location_history", "get_activity", "list_alerts",
                     "get_me", "get_latest_telemetry", "get_device"]:
        key = f"_cache_{fn_name}"
        if key in st.session_state:
            del st.session_state[key]
    for key in list(st.session_state.keys()):
        if key.startswith("_cache_status_"):
            del st.session_state[key]


def register(email: str, full_name: str, password: str, phone: str = "", emergency_contact: str = ""):
    r = _get_client().post("/auth/register", json={
        "email": email,
        "full_name": full_name,
        "password": password,
        "phone": phone or None,
        "emergency_contact": emergency_contact or None,
    })
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    return r.json()


def login(email: str, password: str) -> str:
    r = _get_client().post("/auth/login", json={
        "email": email,
        "password": password,
    })
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    _clear_cache()
    return r.json()["access_token"]


def get_me() -> dict:
    cache_key = "_cache_get_me"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 300:
        return cached["data"]
    try:
        r = _get_client().get("/users/me", headers=_headers())
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def list_devices() -> list[dict]:
    cache_key = "_cache_list_devices"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 30:
        return cached["data"]
    try:
        r = _get_client().get("/devices/", headers=_headers())
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_device(device_id: str) -> dict:
    r = _get_client().get(f"/devices/{device_id}", headers=_headers())
    r.raise_for_status()
    return r.json()


def get_device_status(device_id: str) -> dict:
    cache_key = f"_cache_status_{device_id}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 30:
        return cached["data"]
    try:
        r = _get_client().get(f"/devices/{device_id}/status", headers=_headers())
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_all_device_statuses() -> dict[str, dict]:
    devices = list_devices()
    results = {}
    for dev in devices:
        results[dev["id"]] = get_device_status(dev["id"])
    return results


def pair_device(device_serial: str) -> dict:
    r = _get_client().post("/auth/device/pair", headers=_headers(), params={"device_serial": device_serial})
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    _clear_cache()
    return r.json()


def unpair_device(device_id: str):
    r = _get_client().post(f"/auth/device/unpair/{device_id}", headers=_headers())
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    _clear_cache()


def get_latest_telemetry(device_id: str) -> dict | None:
    r = _get_client().get(f"/telemetry/{device_id}/latest", headers=_headers())
    r.raise_for_status()
    data = r.json()
    return data if data else None


def get_telemetry_history(device_id: str, limit: int = 100) -> list[dict]:
    cache_key = f"_cache_telemetry_{device_id}_{limit}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 60:
        return cached["data"]
    try:
        r = _get_client().get(f"/telemetry/{device_id}/history", headers=_headers(), params={"limit": limit})
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_health_summary(device_id: str, days: int = 7) -> dict:
    cache_key = f"_cache_health_{device_id}_{days}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 60:
        return cached["data"]
    try:
        r = _get_client().get(f"/analytics/{device_id}/health-summary", headers=_headers(), params={"days": days})
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_location_history(device_id: str, limit: int = 100) -> dict:
    cache_key = f"_cache_location_{device_id}_{limit}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 60:
        return cached["data"]
    try:
        r = _get_client().get(f"/analytics/{device_id}/location-history", headers=_headers(), params={"limit": limit})
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_activity(device_id: str, days: int = 7) -> dict:
    cache_key = f"_cache_activity_{device_id}_{days}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 60:
        return cached["data"]
    try:
        r = _get_client().get(f"/analytics/{device_id}/activity", headers=_headers(), params={"days": days})
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def list_alerts(limit: int = 50, resolved: bool | None = None) -> list[dict]:
    params: dict = {"limit": limit}
    if resolved is not None:
        params["resolved"] = resolved
    r = _get_client().get("/alerts/", headers=_headers(), params=params)
    r.raise_for_status()
    return r.json()


def get_active_alerts() -> list[dict]:
    cache_key = "_cache_active_alerts"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached["ts"] < 30:
        return cached["data"]
    try:
        r = _get_client().get("/alerts/active", headers=_headers())
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        _handle_error(e)
    data = r.json()
    st.session_state[cache_key] = {"data": data, "ts": time.time()}
    return data


def resolve_alert(alert_id: str) -> dict:
    r = _get_client().put(f"/alerts/{alert_id}/resolve", headers=_headers())
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    st.session_state.pop("_cache_active_alerts", None)
    return r.json()


def ingest_telemetry(api_key: str, readings: list[dict]) -> dict:
    r = _get_client().post(
        "/telemetry/ingest",
        headers={"X-API-Key": api_key},
        json={"readings": readings},
    )
    if r.status_code >= 400:
        detail = _extract_detail(r)
        raise RuntimeError(detail)
    return r.json()
