# EXT
import streamlit as st


st.set_page_config(
    page_title="AIMS",
    page_icon=":material/notifications_active:",
    layout="centered",
)

x_page = st.navigation(
    [
        st.Page(
            "app_pages/display.py",
            title="Display",
            icon=":material/notifications:",
        ),
        st.Page(
            "app_pages/settings.py",
            title="AWTRIX settings",
            icon=":material/settings:",
        ),
    ],
    position="top",
)

st.title(x_page.title, icon=x_page.icon)
x_page.run()


if __name__ == "__main__":
    pass
