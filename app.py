from core.app_config import configure_app
from core.navigation import run_navigation
from core.theme import load_global_theme
from core.session_state import initialize_session_state


def main() -> None:
    configure_app()
    load_global_theme()
    initialize_session_state()
    run_navigation()


if __name__ == "__main__":
    main()
