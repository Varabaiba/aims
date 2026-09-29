"""Load AIMS runtime settings from the project-level JSON file."""

# INT
from dataclasses import dataclass
import json
from pathlib import Path
from urllib.parse import urlparse


c_settings_file_name = "settings.json"
c_default_awtrix_base_url = "http://127.0.0.1"
c_default_c1_base_url = "http://127.0.0.1:8000"
c_default_sqlite_database_name = "aims.sqlite3"
c_default_forwarding_log_record_limit = 100


class SettingsError(ValueError):
    """Represent an invalid or unusable AIMS settings file."""


@dataclass(frozen=True)
class AimsSettings:
    """Contain the configured AWTRIX target and AIMS database location."""

    awtrix_base_url: str
    c1_base_url: str
    awtrix_token: str | None
    sqlite_database_path: Path
    forwarding_log_record_limit: int


def get_project_path() -> Path:
    """Return the directory that contains the AIMS application files."""
    return Path(__file__).resolve().parent


def get_settings_path() -> Path:
    """Return the project-level path used for runtime settings."""
    return get_project_path() / c_settings_file_name


def normalize_awtrix_base_url(a_value: object) -> str:
    """Validate an AWTRIX HTTP base URL and remove its trailing slash."""
    if not isinstance(a_value, str) or not a_value.strip():
        raise SettingsError("awtrix_base_url must be a non-empty HTTP URL.")

    x_url = a_value.strip().rstrip("/")
    x_parts = urlparse(x_url)
    if x_parts.scheme not in {"http", "https"} or not x_parts.netloc:
        raise SettingsError("awtrix_base_url must be an absolute HTTP or HTTPS URL.")
    if x_parts.query or x_parts.fragment:
        raise SettingsError("awtrix_base_url cannot contain a query string or fragment.")

    return x_url


def get_database_path(a_value: object) -> Path:
    """Resolve the configured SQLite path relative to the project directory."""
    if not isinstance(a_value, str) or not a_value.strip():
        raise SettingsError("sqlite_database_path must be a non-empty file path.")

    x_path = Path(a_value.strip())
    if not x_path.is_absolute():
        x_path = get_project_path() / x_path

    return x_path


def validate_forwarding_log_record_limit(a_value: object) -> int:
    """Validate the number of persisted forwarding records shown by C2."""
    if isinstance(a_value, bool) or not isinstance(a_value, int):
        raise SettingsError("forwarding_log_record_limit must be an integer.")
    if not 1 <= a_value <= 1000:
        raise SettingsError("forwarding_log_record_limit must be between 1 and 1000.")

    return a_value


def load_settings() -> AimsSettings:
    """Load settings or use local defaults when settings.json does not exist."""
    x_settings_path = get_settings_path()
    x_settings_data: dict[str, object] = {}

    if x_settings_path.exists():
        try:
            with x_settings_path.open("r", encoding="utf-8") as x_settings_file:
                x_loaded_data = json.load(x_settings_file)
        except json.JSONDecodeError as x_exception:
            raise SettingsError("settings.json contains invalid JSON.") from x_exception

        if not isinstance(x_loaded_data, dict):
            raise SettingsError("settings.json must contain a JSON object.")

        x_settings_data = x_loaded_data

    x_token_value = x_settings_data.get("awtrix_token")
    if x_token_value is not None and not isinstance(x_token_value, str):
        raise SettingsError("awtrix_token must be a string or null.")

    return AimsSettings(
        awtrix_base_url=normalize_awtrix_base_url(
            x_settings_data.get("awtrix_base_url", c_default_awtrix_base_url)
        ),
        c1_base_url=normalize_awtrix_base_url(
            x_settings_data.get("c1_base_url", c_default_c1_base_url)
        ),
        awtrix_token=x_token_value or None,
        sqlite_database_path=get_database_path(
            x_settings_data.get("sqlite_database_path", c_default_sqlite_database_name)
        ),
        forwarding_log_record_limit=validate_forwarding_log_record_limit(
            x_settings_data.get(
                "forwarding_log_record_limit",
                c_default_forwarding_log_record_limit,
            )
        ),
    )


def save_settings(a_settings: AimsSettings) -> None:
    """Write validated settings as the project-level settings.json document."""
    x_settings_path = get_settings_path()
    x_validated_settings = AimsSettings(
        awtrix_base_url=normalize_awtrix_base_url(a_settings.awtrix_base_url),
        c1_base_url=normalize_awtrix_base_url(a_settings.c1_base_url),
        awtrix_token=a_settings.awtrix_token or None,
        sqlite_database_path=get_database_path(str(a_settings.sqlite_database_path)),
        forwarding_log_record_limit=validate_forwarding_log_record_limit(
            a_settings.forwarding_log_record_limit
        ),
    )
    x_settings_data = {
        "awtrix_base_url": x_validated_settings.awtrix_base_url,
        "c1_base_url": x_validated_settings.c1_base_url,
        "awtrix_token": x_validated_settings.awtrix_token,
        "sqlite_database_path": str(x_validated_settings.sqlite_database_path),
        "forwarding_log_record_limit": x_validated_settings.forwarding_log_record_limit,
    }

    with x_settings_path.open("w", encoding="utf-8") as x_settings_file:
        json.dump(x_settings_data, x_settings_file, indent=2)
        x_settings_file.write("\n")


if __name__ == "__main__":
    pass
