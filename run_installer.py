"""PyInstaller entry point for the packaged Windows application."""

from dubua.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
