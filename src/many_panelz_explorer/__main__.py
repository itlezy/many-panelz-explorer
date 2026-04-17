"""Application entry point for Many Panelz Explorer."""

from __future__ import annotations

import sys

from .app_controller import AppController


def main() -> int:
    """Run the desktop application."""
    try:
        controller = AppController(argv=sys.argv)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return controller.run()


if __name__ == "__main__":
    raise SystemExit(main())
