"""
GreenOps SDK — CLI Entry Point

Run from the command line:
    python -m greenops report
    python -m greenops stats
    python -m greenops sync
"""

import sys
from . import report, sync, stats, configure


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("""
GreenOps CLI — AI Carbon Tracking

Usage:
    python -m greenops report     Show tracking report
    python -m greenops stats      Show raw stats (JSON)
    python -m greenops sync       Sync local data to backend
    python -m greenops help       Show this help message

Environment Variables:
    GREENOPS_SERVER_URL   Backend server URL (default: http://localhost:8000)
    GREENOPS_PROJECT      Default project name (default: default)
    GREENOPS_REGION       Default region (default: global_average)
    GREENOPS_VERBOSE      Enable verbose logging (1/true/yes)
""")
        return

    command = args[0].lower()

    if command == "report":
        source = args[1] if len(args) > 1 else "all"
        report(source=source)

    elif command == "stats":
        import json
        data = stats()
        print(json.dumps(data, indent=2, default=str))

    elif command == "sync":
        print("[GreenOps] Syncing to backend...")
        result = sync()
        print(f"[GreenOps] Synced {result.get('synced', 0)} calls")

    else:
        print(f"[GreenOps] Unknown command: {command}")
        print("Run 'python -m greenops help' for usage")


if __name__ == "__main__":
    main()
