"""Create, inspect, and delete C1 notification schedules."""

# INT
import json

# EXT
import streamlit as st

# OWN
from c2_service import C1RequestError, get_default_notification_payload, request_c1


st.caption("Schedules use five-field UTC CRON expressions: minute hour day month weekday.")
with st.form("create_schedule_form"):
    x_cron_expression = st.text_input("CRON expression (UTC)", value="0 9 * * 1-5", help="Example: */15 * * * * runs every 15 minutes.")
    x_notification_text = st.text_area("Notification payload", value=json.dumps(get_default_notification_payload(), indent=2), height=300)
    x_create_submitted = st.form_submit_button("Create schedule", icon=":material/add:", type="primary")
if x_create_submitted:
    try:
        x_notification = json.loads(x_notification_text)
        if not isinstance(x_notification, dict):
            raise ValueError("Notification payload must be a JSON object.")
        request_c1("POST", "/schedules", {"cron": x_cron_expression, "notification": x_notification})
    except (C1RequestError, ValueError, json.JSONDecodeError) as x_exception:
        st.error(str(x_exception))
    else:
        st.success("Schedule created.")
try:
    x_schedules = request_c1("GET", "/schedules")
except C1RequestError as x_exception:
    st.error(str(x_exception))
    x_schedules = []
if isinstance(x_schedules, list) and x_schedules:
    st.dataframe(x_schedules, hide_index=True)
    x_schedule_ids = [x_schedule["schedule_id"] for x_schedule in x_schedules if isinstance(x_schedule, dict)]
    x_schedule_id = st.selectbox("Schedule to delete", x_schedule_ids)
    if st.button("Delete schedule", icon=":material/delete:"):
        try:
            request_c1("DELETE", f"/schedules/{x_schedule_id}")
        except C1RequestError as x_exception:
            st.error(str(x_exception))
        else:
            st.success("Schedule deleted.")
            st.rerun()
elif isinstance(x_schedules, list):
    st.info("No schedules have been created.")


if __name__ == "__main__":
    pass
