"""Small local entry point for tools that want to launch the popup without a web server."""
from action_popup import main

if __name__ == "__main__":
    raise SystemExit(main())
