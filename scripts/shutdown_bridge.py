from _common import PROJECT_ROOT

from cmo_tutorial.actions import shutdown_bridge
from cmo_tutorial.config import load_config
from cmo_tutorial.protocol import FileProtocol


def main() -> None:
    config = load_config(PROJECT_ROOT / "config.yaml")
    action_id = FileProtocol(config).send(shutdown_bridge())
    print(
        "PyCMO shutdown action queued. "
        f"action_id={action_id}. "
        "CMO will remove the bridge on its next action tick."
    )


if __name__ == "__main__":
    main()
