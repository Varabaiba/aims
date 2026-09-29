# EXT
import streamlit as st

# OWN
from settings_service import load_awtrix_ip_address, save_awtrix_ip_address


st.caption("Set the IP address for the AWTRIX NG informer API.")

try:
    x_current_ip_address = load_awtrix_ip_address()
except ValueError as x_exception:
    x_current_ip_address = ""
    st.error(str(x_exception))

with st.form("awtrix_settings_form"):
    x_awtrix_ip_address = st.text_input(
        "AWTRIX NG informer IP address",
        value=x_current_ip_address,
        placeholder="e.g. 192.168.1.42",
    )
    x_submitted = st.form_submit_button(
        "Save settings",
        icon=":material/save:",
        type="primary",
    )

if x_submitted:
    try:
        x_saved_ip_address = save_awtrix_ip_address(x_awtrix_ip_address)
    except ValueError as x_exception:
        st.error(str(x_exception))
    else:
        st.success(f"AWTRIX informer IP address saved: {x_saved_ip_address}")


if __name__ == "__main__":
    pass
