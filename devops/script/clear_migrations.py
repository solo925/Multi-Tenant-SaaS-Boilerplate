import os
import sys
from pathlib import Path


def main(app_labels: list[str]) -> None:
    # Ensure project root is on sys.path so "config.settings" can be imported
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        import django  # type: ignore
    except ImportError:
        print("Django is not installed in this environment.")
        sys.exit(1)

    django.setup()

    from django.db import connection  # type: ignore

    with connection.cursor() as cursor:
        for app in app_labels:
            cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app])
            print(f"Cleared migration history for app: {app}")

    # Ensure changes are committed for non-autocommit connections
    try:
        connection.commit()
    except Exception:
        pass


if __name__ == "__main__":
    # Default set of local apps we want to reset when starting fresh
    default_apps = [
        "billing",
        "users",
        "shared_users",
        "tenants",
    ]

    # Allow overriding via CLI args: python clear_migrations.py app1 app2 ...
    apps = sys.argv[1:] or default_apps
    main(apps)


