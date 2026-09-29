"""Run the AIMS.C2 Streamlit application."""

# INT
from pathlib import Path
import subprocess
import sys


c_c2_port = 8501


def get_c2_command() -> list[str]:
    """Build the command that starts the C2 Streamlit application."""
    x_application_path = Path(__file__).with_name("streamlit_app.py")
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(x_application_path),
        f"--server.port={c_c2_port}",
    ]



def run_c2() -> None:
    """Start the C2 Streamlit application with its local development defaults."""
    subprocess.run(get_c2_command(), check=True)


if __name__ == "__main__":
    run_c2()
