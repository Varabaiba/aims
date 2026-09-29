"""Forward AIMS requests to the configured AWTRIX NG HTTP API."""

# INT
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib import error, parse, request

# OWN
from settings_service import AimsSettings


c_http_timeout_seconds = 10
c_hop_by_hop_headers = frozenset(
    {
        "connection",
        "content-length",
        "host",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)


class AwtrixRequestError(RuntimeError):
    """Represent an AWTRIX target that cannot be reached."""


@dataclass(frozen=True)
class AwtrixResponse:
    """Contain a proxied AWTRIX HTTP response."""

    status_code: int
    headers: dict[str, str]
    body: bytes


def build_target_url(
    a_base_url: str,
    a_path: str,
    a_query_items: Iterable[tuple[str, str]],
) -> str:
    """Build a target URL while retaining every incoming query parameter."""
    x_path = a_path.lstrip("/")
    x_target_url = f"{a_base_url}/{x_path}" if x_path else a_base_url
    x_query_string = parse.urlencode(list(a_query_items), doseq=True)

    if x_query_string:
        return f"{x_target_url}?{x_query_string}"

    return x_target_url


def filter_headers(a_headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    """Remove HTTP hop-by-hop headers that must not be forwarded."""
    x_filtered_headers: dict[str, str] = {}
    for x_name, x_value in a_headers:
        if x_name.lower() not in c_hop_by_hop_headers:
            x_filtered_headers[x_name] = x_value

    return x_filtered_headers


class AwtrixClient:
    """Forward arbitrary API requests to the current AWTRIX configuration."""

    def __init__(self, a_settings_loader: Callable[[], AimsSettings]) -> None:
        """Store the loader so changed settings apply to subsequent requests."""
        self._settings_loader = a_settings_loader

    def forward(
        self,
        a_method: str,
        a_path: str,
        a_query_items: Iterable[tuple[str, str]],
        a_body: bytes | None,
        a_headers: Iterable[tuple[str, str]],
    ) -> AwtrixResponse:
        """Send a request to AWTRIX and preserve its status, headers, and body."""
        x_settings = self._settings_loader()
        x_target_url = build_target_url(
            x_settings.awtrix_base_url,
            a_path,
            a_query_items,
        )
        x_headers = filter_headers(a_headers)

        if x_settings.awtrix_token:
            x_headers["Authorization"] = f"Bearer {x_settings.awtrix_token}"

        x_request = request.Request(
            x_target_url,
            data=a_body,
            headers=x_headers,
            method=a_method,
        )

        try:
            with request.urlopen(x_request, timeout=c_http_timeout_seconds) as x_response:
                return AwtrixResponse(
                    status_code=x_response.status,
                    headers=filter_headers(x_response.headers.items()),
                    body=x_response.read(),
                )
        except error.HTTPError as x_exception:
            return AwtrixResponse(
                status_code=x_exception.code,
                headers=filter_headers(x_exception.headers.items()),
                body=x_exception.read(),
            )
        except (error.URLError, TimeoutError) as x_exception:
            raise AwtrixRequestError(
                "Could not connect to the configured AWTRIX informer."
            ) from x_exception


if __name__ == "__main__":
    pass
