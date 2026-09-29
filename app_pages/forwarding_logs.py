"""Display the retained C1 forwarding records."""

# EXT
import streamlit as st

# OWN
from c2_service import C1RequestError, request_c1


st.caption("Records for AWTRIX-compatible and simplified notification forwarding.")
if st.button("Refresh logs", icon=":material/refresh:"):
    st.rerun()
try:
    x_records = request_c1("GET", "/forwarding-logs")
except C1RequestError as x_exception:
    st.error(str(x_exception))
else:
    if not isinstance(x_records, list):
        st.error("C1 returned an invalid forwarding-log response.")
    elif not x_records:
        st.info("No forwarding records have been retained yet.")
    else:
        st.dataframe(x_records, hide_index=True)


if __name__ == "__main__":
    pass
