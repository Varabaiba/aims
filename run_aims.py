"""Run both AIMS components under one supervising process."""

# INT
from pathlib import Path
import subprocess
import sys
import time

# OWN
from run_c2 import get_c2_command


def get_c1_command() -> list[str]:
    """Build the command that starts the C1 runner."""
    x_runner_path = Path(__file__).with_name("run_c1.py")
    return [sys.executable, str(x_runner_path)]


def start_component(a_command: list[str]) -> subprocess.Popen[bytes]:
    """Start one AIMS component from the project directory."""
    x_project_path = Path(__file__).parent

    return subprocess.Popen(a_command, cwd=x_project_path)


def stop_component(a_process: subprocess.Popen[bytes]) -> None:
    """Terminate a component process and wait for it to exit."""
    if a_process.poll() is None:
        a_process.terminate()

    try:
        a_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        a_process.kill()
        a_process.wait()


def run_aims() -> None:
    """Start C1 and C2, then stop both services when either exits."""
    x_c1_process = start_component(get_c1_command())
    x_c2_process = start_component(get_c2_command())

    try:
        # Keep both services coupled for local development and simple deployments.
        while x_c1_process.poll() is None and x_c2_process.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_component(x_c1_process)
        stop_component(x_c2_process)


if __name__ == "__main__":
    run_aims()
