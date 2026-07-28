from _common import PROJECT_ROOT
import argparse

from cmo_tutorial.agents import RandomWaypointAgent
from cmo_tutorial.config import load_config
from cmo_tutorial.environment import CMOEnvironment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    cfg = load_config(PROJECT_ROOT / "config.yaml")
    env = CMOEnvironment(cfg)
    agent = RandomWaypointAgent(cfg, seed=args.seed)

    observation, _ = env.reset()
    for step in range(args.steps):
        unit = env.select_controlled_unit(observation)
        action = agent.act(unit, observation)
        result = env.step(action)
        observation = result.observation
        print(
            f"step={step:03d} action={action.name} "
            f"reward={result.reward:.3f} score={result.info['score']}"
        )
        if result.terminated:
            break


if __name__ == "__main__":
    main()
