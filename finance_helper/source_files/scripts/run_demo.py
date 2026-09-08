"""Run the three local services and print a fresh, signed Mini App URL."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.parse import urlencode

from dotenv import load_dotenv
import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]


def check_ports(ports: list[int]) -> None:
    """Fail before starting or migrating if a service is listening."""
    for port in ports:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"Port {port} is busy; choose another --port.")


def wait_ready(process: subprocess.Popen, url: str) -> None:
    deadline = time.monotonic() + 45
    with httpx.Client(trust_env=False, timeout=2) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Service exited before becoming ready: {url}")
            try:
                if client.get(url + "/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
    raise RuntimeError(f"Service startup timed out: {url}")


def stop_services(processes: list[subprocess.Popen]) -> None:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8100,
                        help="Gateway port; finance and analytics use the next two ports")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Verify bootstrap and stop without printing the access token")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65533:
        parser.error("--port must be between 1024 and 65533")
    load_dotenv(ROOT / ".env", override=False)
    if os.getenv("POSTGRES_HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Demo launcher only supports local PostgreSQL")
    check_ports([args.port, args.port + 1, args.port + 2])
    try:
        with psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "finance_db"),
            user=os.getenv("POSTGRES_USER", "finance_user"),
            password=os.getenv("POSTGRES_PASSWORD", "finance_pass"),
            connect_timeout=5,
        ) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as exc:
        raise RuntimeError("Cannot connect to local PostgreSQL. Start it and check "
                           "POSTGRES_* in .env; create the demo database and role first.") from exc
    gateway = f"http://127.0.0.1:{args.port}"
    os.environ.update({
        "GATEWAY_URL": gateway,
        "FINANCE_URL": f"http://127.0.0.1:{args.port + 1}",
        "ANALYTICS_URL": f"http://127.0.0.1:{args.port + 2}",
        "INTERNAL_API_KEY": secrets.token_urlsafe(32),
        "MINIAPP_SIGNING_SECRET": secrets.token_urlsafe(32),
        "BOT_TOKEN": "",  # No Telegram notifications during a local demo.
        "PYTHONUNBUFFERED": "1",
    })
    # A dedicated demo identity, independent of real Telegram users in .env.
    os.environ["DEMO_TELEGRAM_ID"] = "900000099"
    os.environ["DEMO_TELEGRAM_USERNAME"] = "local_demo"
    import seed_demo

    processes = []
    try:
        print("Applying migrations to the configured local PostgreSQL database...", flush=True)
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                       cwd=ROOT / "services/finance-service", check=True)
        for name, port in [("finance-service", args.port + 1),
                           ("analytics-service", args.port + 2),
                           ("api-gateway", args.port)]:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                 "--port", str(port), "--no-access-log"],
                cwd=ROOT / "services" / name,
            )
            processes.append(process)
            wait_ready(process, f"http://127.0.0.1:{port}")
        seed_demo.main()
        params = {"telegram_id": seed_demo.TELEGRAM_ID}
        workspace = seed_demo.request("GET", "/workspaces/active", params=params)
        params["workspace_id"] = workspace["id"]
        token = seed_demo.request("GET", "/miniapp/token", params=params)["token"]
        query = urlencode({"token": token})
        with httpx.Client(trust_env=False, timeout=30) as client:
            response = client.get(f"{gateway}/miniapp/public/bootstrap?{query}")
            if response.status_code != 200 or "dashboard" not in response.json():
                raise RuntimeError("Mini App bootstrap failed; inspect service errors above.")
        if args.smoke_test:
            print("PASS: migrations, services, demo user and Mini App bootstrap.")
            return 0
        print(f"\nOpen in your browser:\n{gateway}/miniapp/app?{query}\n", flush=True)
        print("Keep this terminal open. Ctrl+C stops all three services.\n"
              "Restart this command for a fresh link; do not share the signed URL.", flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        raise RuntimeError("A service exited; restart the demo after checking its error.")
    finally:
        stop_services(processes)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nDemo stopped.")
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
