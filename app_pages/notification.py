"""Build and send typed AWTRIX notification payloads through C1."""

# INT
import json

# EXT
import streamlit as st

# OWN
from c2_service import (
    C1RequestError,
    load_last_notification,
    request_c1,
    save_last_notification,
)


def parse_integer_list(a_value: str, a_field_name: str) -> list[int]:
    """Parse comma-separated integer chart values."""
    if not a_value.strip():
        return []
    try:
        return [int(x_item.strip()) for x_item in a_value.split(",")]
    except ValueError as x_exception:
        raise ValueError(f"{a_field_name} must contain comma-separated integers.") from x_exception


def parse_json_array(a_value: str, a_field_name: str) -> list[object]:
    """Parse an optional structured AWTRIX array field."""
    if not a_value.strip():
        return []
    x_data = json.loads(a_value)
    if not isinstance(x_data, list):
        raise ValueError(f"{a_field_name} must be a JSON array.")
    return x_data


st.caption("Typed controls map directly to AWTRIX notification fields. Use each help icon for field details.")
try:
    x_last_notification = load_last_notification()
except (OSError, ValueError, json.JSONDecodeError) as x_exception:
    x_last_notification = {}
    st.warning(f"Could not load last notification values: {x_exception}")
if st.session_state.pop("notification_clear_form", False):
    x_last_notification = {}

with st.form("notification_form"):
    with st.container(border=True):
        st.subheader("Text and scrolling")
        x_text = st.text_area("Text", value=str(x_last_notification.get("text", "")), help="Message shown on the matrix.")
        x_text_case = st.selectbox("Text case", ["inherit", "upper", "asTyped"], help="Casing applied by AWTRIX.")
        x_font = st.selectbox("Font", ["small", "large"], help="Matrix font size.")
        x_text_color = st.color_picker("Text color", "#FFFFFF", help="Text color unless a palette is used.")
        x_blink = st.number_input("Text blink period (ms)", min_value=0, value=0, step=100, help="Zero disables blinking.")
        x_fade = st.number_input("Text fade period (ms)", min_value=0, value=0, step=100, help="Zero disables fading.")
        x_center = st.checkbox("Center text", value=True, help="Centers text that fits.")
        x_offset = st.number_input("Text X offset", value=0, step=1, help="Horizontal pixel offset.")
        x_in_front = st.checkbox("Draw text in front", help="Draw text over charts and drawing commands.")
        with st.expander("Scroll settings"):
            x_scroll_mode = st.selectbox("Scroll mode", ["wrap", "static", "loop", "bounce"], help="Text movement behavior.")
            x_scroll_direction = st.selectbox("Scroll direction", ["left", "right"], help="Animation direction.")
            x_scroll_entry = st.selectbox("Scroll entry", ["inline", "offscreen"], help="Initial text position.")
            x_scroll_fits = st.selectbox("When text fits", ["static", "scroll"], help="Whether short text moves.")
            x_scroll_speed = st.number_input("Scroll speed (%)", min_value=0, value=100, help="Base scroll-rate percentage.")
            x_scroll_gap = st.number_input("Scroll gap (px)", min_value=0, value=8, help="Loop-mode gap.")
            x_scroll_hold = st.number_input("Scroll hold (ms)", min_value=0, value=1000, step=100, help="Pause between cycles.")

    with st.container(border=True):
        st.subheader("Icons")
        x_icon = st.text_input("Primary icon", help="Icon ID or inline base64 JPEG/GIF.")
        x_icon_mode = st.selectbox("Primary icon mode", ["fixed", "pushOnce", "push"], help="How scrolling text moves the icon.")
        x_icon_offset = st.number_input("Primary icon X offset", value=0, step=1, help="Horizontal icon offset.")
        x_icon_gap = st.number_input("Primary icon gap (px)", min_value=0, max_value=128, value=1, help="Blank columns before text.")
        x_icons = st.text_area("Additional icons", placeholder='[{"icon":"weather","x":0,"y":0}]', help="JSON array of up to four icon, x, y objects.")

    with st.container(border=True):
        st.subheader("Timing and behavior")
        x_duration = st.number_input("Duration (ms)", min_value=0, value=7000, step=100, help="Display duration unless held.")
        x_lifetime = st.number_input("Lifetime (ms)", min_value=0, value=0, step=1000, help="Parsed but ignored for notifications.")
        x_expiry = st.selectbox("Lifetime expiry", ["remove", "mark"], help="Parsed but ignored for notifications.")
        x_repeat = st.number_input("Scroll repetitions", min_value=0, value=0, help="Completed scroll cycles before expiry.")
        x_name = st.text_input("Notification name", help="Name used for targeted dismissal.")
        x_hold = st.checkbox("Hold notification", help="Keep visible until dismissed.")
        x_stack = st.checkbox("Stack notification", value=True, help="Queue behind the active notification.")
        x_wakeup = st.checkbox("Wake display", help="Show while display power is off.")

    with st.container(border=True):
        st.subheader("Visuals")
        x_background = st.color_picker("Background color", "#000000", help="Canvas fill when no effect runs.")
        x_bar_chart = st.text_input("Bar chart values", help="Comma-separated integers, maximum 16.")
        x_line_chart = st.text_input("Line chart values", help="Comma-separated integers, maximum 16.")
        x_autoscale = st.checkbox("Autoscale charts", value=True, help="Scale chart to data range.")
        x_chart_color = st.color_picker("Chart color", "#FFFFFF", help="Color for bars and lines.")
        x_progress = st.number_input("Progress (%)", min_value=-1, max_value=100, value=-1, help="Negative hides the progress bar.")
        x_progress_color = st.color_picker("Progress fill color", "#00FF00", help="Completed progress segment.")
        x_track_color = st.color_picker("Progress track color", "#FFFFFF", help="Unfilled progress segment.")
        x_effect = st.text_input("Background effect", help="AWTRIX effect name; empty disables it.")
        x_effect_speed = st.number_input("Effect speed", min_value=0.1, max_value=10.0, value=1.0, step=0.1, help="Effect and overlay speed multiplier.")
        x_overlay = st.selectbox("Overlay", ["", "rain", "snow", "drizzle", "storm", "thunder", "frost"], help="Weather overlay.")
        x_palette = st.selectbox("Palette", ["", "Cloud", "Lava", "Ocean", "Forest", "Stripe", "Party", "Heat", "Rainbow"], help="Built-in palette or none.")
        x_blend = st.checkbox("Blend palette", value=True, help="Interpolate palette colors.")
        x_span = st.number_input("Palette span (px)", min_value=0, value=0, help="Pixels per palette pass.")
        x_palette_speed = st.number_input("Palette speed", min_value=0.0, max_value=10.0, value=0.0, step=0.1, help="Palette passes per second.")

    with st.container(border=True):
        st.subheader("Sound and custom drawing")
        x_sound = st.text_input("Sound", help="MP3, melody, or DFPlayer track.")
        x_rtttl = st.text_input("RTTTL sound", help="Inline melody that overrides Sound.")
        x_sound_loop = st.checkbox("Loop sound", help="Repeat sound while active.")
        x_draw = st.text_area("Draw commands", placeholder='[["rect",0,0,32,8,"#202020"]]', help="Optional JSON array of AWTRIX drawing command arrays.")
    x_submitted = st.form_submit_button("Send notification", icon=":material/send:", type="primary")
    x_clear_submitted = st.form_submit_button("Clear form", icon=":material/clear:")

if x_clear_submitted:
    # Reset transient widget state without changing last_notification.json.
    st.session_state.clear()
    st.session_state["notification_clear_form"] = True
    st.rerun()

if x_submitted:
    try:
        x_payload = {"text":x_text,"textCase":x_text_case,"font":x_font,"textColor":x_text_color,"textBlinkMs":int(x_blink),"textFadeMs":int(x_fade),"textCenter":x_center,"scroll":{"mode":x_scroll_mode,"direction":x_scroll_direction,"entry":x_scroll_entry,"whenFits":x_scroll_fits,"speed":int(x_scroll_speed),"gap":int(x_scroll_gap),"holdMs":int(x_scroll_hold)},"textOffsetX":int(x_offset),"textInFront":x_in_front,"icon":x_icon,"iconMode":x_icon_mode,"iconOffsetX":int(x_icon_offset),"iconGap":int(x_icon_gap),"icons":parse_json_array(x_icons,"Additional icons"),"durationMs":int(x_duration),"lifetimeMs":int(x_lifetime),"lifetimeExpiry":x_expiry,"repeat":int(x_repeat),"backgroundColor":x_background,"barChart":parse_integer_list(x_bar_chart,"Bar chart values"),"lineChart":parse_integer_list(x_line_chart,"Line chart values"),"chartAutoscale":x_autoscale,"chartColor":x_chart_color,"progress":int(x_progress),"progressColor":x_progress_color,"progressTrackColor":x_track_color,"effect":x_effect,"effectSpeed":float(x_effect_speed),"palette":x_palette or None,"paletteBlend":x_blend,"paletteSpan":int(x_span),"paletteSpeed":float(x_palette_speed),"overlay":x_overlay,"draw":parse_json_array(x_draw,"Draw commands"),"name":x_name,"hold":x_hold,"stack":x_stack,"wakeup":x_wakeup,"sound":x_sound,"soundRtttl":x_rtttl,"soundLoop":x_sound_loop}
        request_c1("POST", "/api/v1/notifications", x_payload)
    except (C1RequestError, ValueError, json.JSONDecodeError) as x_exception:
        st.error(str(x_exception))
    else:
        save_last_notification(x_payload)
        st.success("Notification accepted by C1.")


if __name__ == "__main__":
    pass
