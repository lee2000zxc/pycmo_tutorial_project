from _common import PROJECT_ROOT
import argparse

from cmo_tutorial.actions import set_course_speed_altitude
from cmo_tutorial.config import load_config
from cmo_tutorial.protocol import FileProtocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", required=True)
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--altitude", type=float)
    args = parser.parse_args()

    cfg = load_config(PROJECT_ROOT / "config.yaml")
    action = set_course_speed_altitude(
        cfg.scenario.player_side,
        args.unit,
        args.lat,
        args.lon,
        args.speed,
        args.altitude,
    )
    FileProtocol(cfg).send(action)
    print(f"Action written: {action.name}")
    print(f"Path: {cfg.action_path}")


if __name__ == "__main__":
    main()
