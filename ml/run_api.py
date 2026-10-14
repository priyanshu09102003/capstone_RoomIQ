"""CLI runner to launch the RoomIQ FastAPI backend service."""

import argparse
import sys
from pathlib import Path
import uvicorn

# Ensure ml directory is on sys.path
ml_dir = Path(__file__).resolve().parent
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))


def main():
    parser = argparse.ArgumentParser(description="Launch the RoomIQ FastAPI backend service.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for local development")
    args = parser.parse_args()

    print(f"Starting RoomIQ API on http://{args.host}:{args.port} (reload={args.reload})...")
    uvicorn.run("src.api.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
