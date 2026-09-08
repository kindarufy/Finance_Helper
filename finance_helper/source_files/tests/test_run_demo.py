"""Local demo launcher checks without starting application services."""
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location(
    "run_demo", Path(__file__).resolve().parents[1] / "scripts/run_demo.py"
)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_occupied_port_is_reported():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with pytest.raises(RuntimeError, match="busy"):
            demo.check_ports([listener.getsockname()[1]])


def test_cleanup_stops_only_owned_child():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        demo.stop_services([child])
        assert child.poll() is not None
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_failed_child_is_reported_without_waiting_for_timeout():
    child = subprocess.Popen([sys.executable, "-c", "raise SystemExit(1)"])
    child.wait()
    with pytest.raises(RuntimeError, match="exited"):
        demo.wait_ready(child, "http://127.0.0.1:1")
