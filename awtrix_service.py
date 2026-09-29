"""Send notifications to the configured AWTRIX NG HTTP API."""

# INT
import json
from urllib import error, request

# OWN
from settings_service import validate_awtrix_ip_address


c_notification_path = "/api/v1/notifications"
c_http_timeout_seconds = 5
c_buzzer_rtttl = "Bell:d=4,o=5,b=120:c,e,g"


class AwtrixRequestError(RuntimeError):
    """Represent a failed request to an AWTRIX device."""


def build_notification_payload(
    a_text: str,
    a_icon_name: str,
    a_duration_seconds: int,
    a_buzzer_enabled: bool,
) -> dict[str, str | int]:
    """Build a valid AWTRIX NG notification payload from UI input."""
    if not a_text.strip():
        raise ValueError("Enter text to display before sending the notification.")

    if isinstance(a_duration_seconds, bool) or a_duration_seconds < 1:
        raise ValueError("Notification timeout must be at least one second.")

    # AWTRIX expects the display duration in milliseconds.
    x_payload = {
        "text": a_text,
        "durationMs": a_duration_seconds * 1000,
    }

    if a_icon_name.strip():
        x_payload["icon"] = a_icon_name.strip()

    if a_buzzer_enabled:
        # The current API plays a buzzer through an inline RTTTL melody.
        x_payload["soundRtttl"] = c_buzzer_rtttl

    return x_payload


def get_notification_url(a_ip_address: str) -> str:
    """Build the notification endpoint URL for an IPv4 or IPv6 AWTRIX address."""
    x_ip_address = validate_awtrix_ip_address(a_ip_address)
    x_host = f"[{x_ip_address}]" if ":" in x_ip_address else x_ip_address
    return f"http://{x_host}{c_notification_path}"


def send_notification(
    a_ip_address: str,
    a_text: str,
    a_icon_name: str,
    a_duration_seconds: int,
    a_buzzer_enabled: bool,
) -> None:
    """POST one notification to AWTRIX and raise a clear error when it fails."""
    x_url = get_notification_url(a_ip_address)
    x_payload = build_notification_payload(
        a_text,
        a_icon_name,
        a_duration_seconds,
        a_buzzer_enabled,
    )
    x_request = request.Request(
        x_url,
        data=json.dumps(x_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        # Read the response so the connection is released before the function returns.
        with request.urlopen(x_request, timeout=c_http_timeout_seconds) as x_response:
            x_response.read()
            x_status_code = x_response.status
    except error.HTTPError as x_exception:
        raise AwtrixRequestError(
            f"AWTRIX rejected the notification with HTTP {x_exception.code}."
        ) from x_exception
    except (error.URLError, TimeoutError) as x_exception:
        raise AwtrixRequestError(
            "Could not connect to the configured AWTRIX informer."
        ) from x_exception

    if x_status_code != 200:
        raise AwtrixRequestError(
            f"AWTRIX returned unexpected HTTP status {x_status_code}."
        )


if __name__ == "__main__":
    pass
