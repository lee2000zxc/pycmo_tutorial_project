from _common import PROJECT_ROOT
import argparse

from cmo_tutorial.agents import Tutorial3RouteAgent
from cmo_tutorial.config import load_config
from cmo_tutorial.environment import CMOEnvironment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=50)
    args = parser.parse_args()

    cfg = load_config(PROJECT_ROOT / "config.yaml")
    env = CMOEnvironment(cfg)
    agent = Tutorial3RouteAgent(cfg)

    observation, _ = env.reset()
    for step in range(args.steps):
        unit = env.select_controlled_unit(observation)
        action = agent.act(unit, observation)
        result = env.step(action)
        observation = result.observation
        print(
            f"step={step:03d} waypoint={agent.waypoint_index} "
            f"action={action.name} reward={result.reward:.3f}"
        )
        if result.terminated:
            print("Scenario ended.")
            break


if __name__ == "__main__":
    main()
