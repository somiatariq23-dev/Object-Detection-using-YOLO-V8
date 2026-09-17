"""
Unified launcher: builds the React frontend (if needed) then starts the FastAPI server.
Usage:
    python run.py              # build frontend if dist is missing, then serve on :8000
    python run.py --rebuild    # force rebuild frontend even if dist exists
    python run.py --port 9000  # custom port
"""

import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"


def build_frontend(force: bool = False):
    if DIST_DIR.exists() and not force:
        print("[run.py] Frontend dist already exists. Skipping build. Use --rebuild to force.")
        return

    print("[run.py] Building React frontend...")

    # Ensure node_modules exist
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[run.py] node_modules not found. Running npm install...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            shell=True
        )
        if result.returncode != 0:
            print("[run.py] ERROR: npm install failed. Make sure Node.js is installed.")
            sys.exit(1)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        shell=True
    )
    if result.returncode != 0:
        print("[run.py] ERROR: Frontend build failed.")
        sys.exit(1)

    print("[run.py] Frontend built successfully.")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    print(f"\n[run.py] Starting EyeSight AI server...")
    print(f"  Dashboard  -> http://localhost:{port}")
    print(f"  API Docs   -> http://localhost:{port}/docs")
    print(f"  Health     -> http://localhost:{port}/api/v1/health\n")
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EyeSight AI Unified Launcher")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild of React frontend")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    args = parser.parse_args()

    build_frontend(force=args.rebuild)
    start_server(host=args.host, port=args.port)
