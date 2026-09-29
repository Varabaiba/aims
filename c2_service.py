"""Call C1 and provide default AWTRIX notification values for C2."""

# INT
import json
from pathlib import Path
from urllib import error, request

# OWN
from settings_service import load_settings


c_http_timeout_seconds = 10
c_last_notification_file_name = "last_notification.json"


class C1RequestError(RuntimeError):
    """Represent a C1 API request that could not be completed."""


def get_last_notification_path() -> Path:
    """Return the project file that stores the last accepted notification payload."""
    return Path(__file__).resolve().with_name(c_last_notification_file_name)


def load_last_notification() -> dict[str, object]:
    """Load the last accepted payload, or return an empty mapping when absent."""
    x_path = get_last_notification_path()
    if not x_path.exists():
        return {}
    with x_path.open("r", encoding="utf-8") as x_file:
        x_payload = json.load(x_file)
    if not isinstance(x_payload, dict):
        raise ValueError("last_notification.json must contain a JSON object.")
    return x_payload


def save_last_notification(a_payload: dict[str, object]) -> None:
    """Persist the payload accepted by C1 for the next C2 startup."""
    with get_last_notification_path().open("w", encoding="utf-8") as x_file:
        json.dump(a_payload, x_file, indent=2)
        x_file.write("\n")


def get_default_notification_payload() -> dict[str, object]:
    """Return all AWTRIX notification fields with their documented defaults."""
    return {"text":"","textCase":"inherit","font":"small","textColor":"#FFFFFF","textBlinkMs":0,"textFadeMs":0,"textCenter":True,"scroll":{"mode":"wrap","direction":"left","entry":"inline","whenFits":"static","speed":100,"gap":8,"holdMs":1000},"textOffsetX":0,"textInFront":False,"icon":"","iconMode":"fixed","iconOffsetX":0,"iconGap":1,"icons":[],"durationMs":7000,"lifetimeMs":0,"lifetimeExpiry":"remove","repeat":0,"backgroundColor":"#000000","barChart":[],"lineChart":[],"chartAutoscale":True,"chartColor":"#FFFFFF","progress":-1,"progressColor":"#00FF00","progressTrackColor":"#FFFFFF","effect":"","effectSpeed":1.0,"palette":None,"paletteBlend":True,"paletteSpan":0,"paletteSpeed":0.0,"overlay":"","draw":[],"name":"","hold":False,"stack":True,"wakeup":False,"sound":"","soundRtttl":"","soundLoop":False}


def request_c1(a_method: str, a_path: str, a_payload: object | None = None) -> object:
    """Request C1 JSON and turn transport or HTTP failures into clear errors."""
    x_settings = load_settings()
    x_data = None if a_payload is None else json.dumps(a_payload).encode("utf-8")
    x_headers = {"Accept": "application/json"}
    if x_data is not None:
        x_headers["Content-Type"] = "application/json"
    x_request = request.Request(f"{x_settings.c1_base_url}{a_path}", data=x_data, headers=x_headers, method=a_method)
    try:
        with request.urlopen(x_request, timeout=c_http_timeout_seconds) as x_response:
            x_body = x_response.read()
    except error.HTTPError as x_exception:
        raise C1RequestError(f"C1 returned HTTP {x_exception.code}: {x_exception.read().decode('utf-8', errors='replace')}") from x_exception
    except (error.URLError, TimeoutError) as x_exception:
        raise C1RequestError("Could not connect to the configured C1 server.") from x_exception
    if not x_body:
        return None
    try:
        return json.loads(x_body)
    except json.JSONDecodeError as x_exception:
        raise C1RequestError("C1 returned an invalid JSON response.") from x_exception


if __name__ == "__main__":
    pass
