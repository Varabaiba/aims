"""Load and save the locally configured AWTRIX informer address."""

# INT
import ipaddress
import json
from pathlib import Path


c_config_file_name = "aims_config.json"
c_default_awtrix_ip_address = "127.0.0.1"


def get_config_path() -> Path:
    """Return the project-level path used for the AIMS configuration file."""
    return Path(__file__).resolve().parent / c_config_file_name


def validate_awtrix_ip_address(a_ip_address: str) -> str:
    """Validate and normalize an IPv4 or IPv6 address for the AWTRIX informer."""
    try:
        return str(ipaddress.ip_address(a_ip_address.strip()))
    except ValueError as x_exception:
        raise ValueError("Enter a valid IPv4 or IPv6 address.") from x_exception


def load_awtrix_ip_address() -> str:
    """Load the saved AWTRIX address, or return the local default when unset."""
    x_config_path = get_config_path()

    if not x_config_path.exists():
        return c_default_awtrix_ip_address

    try:
        with x_config_path.open("r", encoding="utf-8") as x_config_file:
            x_config_data = json.load(x_config_file)
    except json.JSONDecodeError as x_exception:
        raise ValueError("The AIMS configuration file contains invalid JSON.") from x_exception

    if not isinstance(x_config_data, dict):
        raise ValueError("The AIMS configuration file must contain a JSON object.")

    x_ip_address = x_config_data.get("awtrix_ip_address")
    if not isinstance(x_ip_address, str):
        raise ValueError("The AIMS configuration file has no valid AWTRIX IP address.")

    return validate_awtrix_ip_address(x_ip_address)


def save_awtrix_ip_address(a_ip_address: str) -> str:
    """Validate and persist the AWTRIX informer address in the project folder."""
    x_validated_ip_address = validate_awtrix_ip_address(a_ip_address)
    x_config_path = get_config_path()
    x_config_data = {"awtrix_ip_address": x_validated_ip_address}

    with x_config_path.open("w", encoding="utf-8") as x_config_file:
        json.dump(x_config_data, x_config_file, indent=2)
        x_config_file.write("\n")

    return x_validated_ip_address


if __name__ == "__main__":
    pass
