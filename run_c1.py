"""Run the AIMS.C1 FastAPI service."""

# EXT
import uvicorn

# OWN
from c1_app import c_app


c_c1_host = "127.0.0.1"
c_c1_port = 8000


def run_c1() -> None:
    """Start the C1 API server with its local development defaults."""
    uvicorn.run(c_app, host=c_c1_host, port=c_c1_port)


if __name__ == "__main__":
    run_c1()
