"""Production smoke checks. Docker mode also builds the real image.

python tools/verify_deploy.py --server gunicorn
python tools/verify_deploy.py --server docker
python tools/verify_deploy.py --server flask  # Windows local HTTP check only
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def check_http(port, alive):
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 45
    while True:
        if not alive():
            raise RuntimeError("Server exited before becoming healthy")
        try:
            with urlopen(base + "/health", timeout=2) as response:
                assert response.status == 200
                assert json.load(response) == {"status": "ok", "service": "darwin-web"}
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError("Healthcheck did not become ready in 45 seconds")
            time.sleep(0.25)
    for path in ["/", "/features", "/case-study", "/architecture", "/app", "/static/js/boot.js", "/static/css/styles.css"]:
        with urlopen(base + path, timeout=5) as response:
            assert response.status == 200, path
    print(f"PASS: /health HTTP 200 and 7 routes/assets on port {port}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", choices=["gunicorn", "docker", "flask"], default="gunicorn")
    args = parser.parse_args()
    port = free_port()
    env = dict(os.environ, PORT=str(port), SITE_URL="http://127.0.0.1:" + str(port))
    if args.server == "docker":
        if not shutil.which("docker"):
            parser.error("Docker is required; no image build or production check was executed")
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL)
        # A unique tag prevents overwriting another local build.
        tag = "darwin-verify:" + str(os.getpid())
        subprocess.run(["docker", "build", "--tag", tag, "."], cwd=ROOT, check=True)
        cid = None
        try:
            cid = subprocess.check_output(["docker", "run", "--detach", "--env", "PORT=18765", "--env", "SITE_URL=http://localhost", "--publish", f"127.0.0.1:{port}:18765", tag], text=True).strip()
            running = lambda: subprocess.check_output(["docker", "inspect", "--format", "{{.State.Running}}", cid], text=True).strip() == "true"
            check_http(port, running)
            user = subprocess.check_output(["docker", "exec", cid, "id", "-u"], text=True).strip()
            assert user != "0", "Container must run as non-root"
            print("PASS: image built; default CMD honors PORT=18765; non-root user")
        finally:
            if cid:
                subprocess.run(["docker", "logs", cid], check=False)
                subprocess.run(["docker", "rm", "--force", cid], check=False)
    else:
        if args.server == "gunicorn" and os.name == "nt":
            parser.error("Gunicorn requires Unix/Linux; use Docker or a Linux runner")
        command = [sys.executable, "-m", "gunicorn", "app:app"] if args.server == "gunicorn" else [sys.executable, "app.py"]
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                check_http(port, lambda: process.poll() is None)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                log.seek(0)
                print(log.read())


if __name__ == "__main__":
    main()
