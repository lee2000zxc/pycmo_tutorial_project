from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
from cmo_tutorial.environment import CMOEnvironment


def main() -> None:
    config = load_config(PROJECT_ROOT / "config.yaml")
    environment = CMOEnvironment(config)

    print("CMO File > Load Recent의 첫 시나리오를 불러옵니다...")
    environment.restart_scenario()
    observation, _ = environment.reset()
    print(
        "재시작 완료: "
        f"title={observation.title!r}, "
        f"time={observation.scenario_time}"
    )


if __name__ == "__main__":
    main()
