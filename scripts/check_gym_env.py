from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv


def main():
    cfg = load_config(PROJECT_ROOT / "config.yaml")
    env = CMOTutorialGymEnv(cfg)
    observation, info = env.reset()
    print("Observation:", observation)
    print("Info:", info)
    action = env.action_space.sample()
    print("Sample action:", action)
    result = env.step(action)
    print("Step result:", result)


if __name__ == "__main__":
    main()
