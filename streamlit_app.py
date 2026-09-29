"""AIMS.C2 Streamlit application entry point."""

# EXT
import streamlit as st


st.set_page_config(page_title="AIMS C2", page_icon=":material/notifications:")

x_page = st.navigation(
    [
        st.Page("app_pages/configuration.py", title="Configuration", icon=":material/settings:"),
        st.Page("app_pages/notification.py", title="Send notification", icon=":material/send:"),
        st.Page("app_pages/forwarding_logs.py", title="Forwarding logs", icon=":material/receipt_long:"),
        st.Page("app_pages/schedules.py", title="Schedules", icon=":material/calendar_clock:"),
    ],
    position="top",
)

st.title(x_page.title, icon=x_page.icon)
x_page.run()


if __name__ == "__main__":
    pass
