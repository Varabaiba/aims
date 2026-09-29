# EXT
import streamlit as st

# OWN
from awtrix_service import AwtrixRequestError, send_notification
from settings_service import load_awtrix_ip_address


st.caption("Prepare a notification for the configured AWTRIX informer.")

with st.form("display_input_form"):
    x_display_text = st.text_area(
        "Text to display",
        placeholder="Enter the message for AWTRIX",
        key="display_text",
    )
    x_icon_name = st.text_input(
        "Icon name to show",
        placeholder="e.g. weather_sunny",
        key="display_icon_name",
    )
    x_buzzer_enabled = st.checkbox("Sound the buzzer", key="display_buzzer_enabled")
    x_duration_seconds = st.number_input(
        "Notification timeout (seconds)",
        min_value=1,
        max_value=3600,
        value=7,
        step=1,
        key="display_duration_seconds",
    )
    x_submitted = st.form_submit_button(
        "Send notification",
        icon=":material/send:",
        type="primary",
    )

if x_submitted:
    # Keep the submitted values available for the current browser session.
    st.session_state["display_request"] = {
        "text": x_display_text,
        "icon_name": x_icon_name,
        "buzzer": x_buzzer_enabled,
        "duration_seconds": x_duration_seconds,
    }

    try:
        x_awtrix_ip_address = load_awtrix_ip_address()
        with st.spinner("Sending notification to AWTRIX..."):
            send_notification(
                x_awtrix_ip_address,
                x_display_text,
                x_icon_name,
                x_duration_seconds,
                x_buzzer_enabled,
            )
    except (AwtrixRequestError, ValueError) as x_exception:
        st.error(str(x_exception))
    else:
        st.success("Notification sent to AWTRIX.")


if __name__ == "__main__":
    pass
