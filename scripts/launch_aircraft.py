from _common import PROJECT_ROOT
import argparse

from cmo_tutorial.actions import launch
from cmo_tutorial.config import load_config
from cmo_tutorial.protocol import FileProtocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--unit",
        required=True,
        help="출격시킬 항공기 이름",
    )
    args = parser.parse_args()

    config = load_config(
        PROJECT_ROOT / "config.yaml"
    )

    action = launch(
        side=config.scenario.player_side,
        unit_name=args.unit,
        enabled=True,
    )

    protocol = FileProtocol(config)
    protocol.send(action)

    print(f"Launch action written: {args.unit}")
    print(f"Action file: {config.action_path}")


if __name__ == "__main__":
    main()