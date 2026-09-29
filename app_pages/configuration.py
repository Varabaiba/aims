"""Manage the settings shared by AIMS.C1 and AIMS.C2."""

# INT
from pathlib import Path

# EXT
import streamlit as st

# OWN
from settings_service import AimsSettings, SettingsError, load_settings, save_settings


try:
    x_settings = load_settings()
except SettingsError as x_exception:
    st.error(str(x_exception))
    st.stop()

st.caption("These values are stored in the project-level settings.json file.")
with st.form("configuration_form"):
    x_awtrix_base_url = st.text_input("AWTRIX base URL", value=x_settings.awtrix_base_url)
    x_c1_base_url = st.text_input("C1 API URL", value=x_settings.c1_base_url)
    x_awtrix_token = st.text_input("AWTRIX token", value=x_settings.awtrix_token or "", type="password")
    x_sqlite_database_path = st.text_input("SQLite database path", value=str(x_settings.sqlite_database_path))
    x_log_record_limit = st.number_input("Forwarding log records to retain", min_value=1, max_value=1000, value=x_settings.forwarding_log_record_limit, step=1)
    x_submitted = st.form_submit_button("Save configuration", icon=":material/save:", type="primary")

if x_submitted:
    try:
        x_new_settings = AimsSettings(x_awtrix_base_url.strip().rstrip("/"), x_c1_base_url.strip().rstrip("/"), x_awtrix_token.strip() or None, Path(x_sqlite_database_path.strip()), int(x_log_record_limit))
        save_settings(x_new_settings)
    except (OSError, ValueError) as x_exception:
        st.error(str(x_exception))
    else:
        st.success("Configuration saved.")


if __name__ == "__main__":
    pass
